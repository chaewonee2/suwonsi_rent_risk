import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from openai import OpenAI

st.set_page_config(layout="wide")
st.title("🏠 수원시 전세 매물 지도 (클릭 상세보기)")

# OpenAI 클라이언트
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_test.csv")

    if "구" not in df.columns or "시" not in df.columns:
        if "시군구" in df.columns:
            df[["시", "구"]] = df["시군구"].str.split(" ", n=1, expand=True)

    if "전세가율" in df.columns:
        df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)

    return df.dropna(subset=["위도", "경도"])

df = load_data()

# 예시 지역 데이터프레임 (실제 지역 데이터로 대체)
region_df = pd.DataFrame([
    {"구":"영통구","인구":"30만 명","주요시설":"광교호수공원, 컨벤션센터","교통":"신분당선 광교중앙역"},
    {"구":"장안구","인구":"20만 명","주요시설":"수원KT위즈파크","교통":"1호선 성균관대역"}
])

# --- 지도 + 상세 정보 ---
col1, col2 = st.columns([2, 1])

with col1:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df.iterrows():
        danji = row.get("단지명", "")
        floor = row.get("층", "")
        unique_key = f"{danji}_{floor}"

        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=f"{danji} ({row.get('위험도점수','N/A')}점)",
            popup=unique_key
        ).add_to(marker_cluster)

        df.at[i, "unique_key"] = unique_key

    st_data = st_folium(m, width=900, height=600)

with col2:
    st.subheader("📋 매물 상세정보")

    if st_data and st_data.get("last_object_clicked_popup"):
        clicked_key = st_data["last_object_clicked_popup"]
        row_match = df[df["unique_key"] == clicked_key]

        if not row_match.empty:
            prop = row_match.iloc[0].to_dict()
            st.session_state["selected_property"] = prop

            # 지역 매칭
            reg_match = region_df[region_df["구"] == prop["구"]]
            if not reg_match.empty:
                st.session_state["selected_region"] = reg_match.iloc[0].to_dict()

# --- 자동 GPT 해석 ---
if "selected_property" in st.session_state and "selected_region" in st.session_state:
    prop = st.session_state["selected_property"]
    reg = st.session_state["selected_region"]

    st.subheader("🌍 지역정보")
    st.write(reg)

    prompt = f"""
    [매물 정보]
    - 단지명: {prop['단지명']}
    - 위치: {prop['구']}
    - 거래금액: {prop['거래금액.만원.']} 만원
    - 전세가율: {prop['전세가율']}%
    - 위험도점수: {prop.get('위험도점수','N/A')}

    [지역 정보]
    - 인구: {reg['인구']}
    - 주요시설: {reg['주요시설']}
    - 교통: {reg['교통']}

    위 정보를 바탕으로:
    1) 투자 관점에서 이 매물과 지역을 해석해줘.
    2) 안전 관점에서 이 매물과 지역을 해석해줘.
    """

    st.subheader("🤖 AI 자동 해석")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    st.markdown(response.choices[0].message.content)
