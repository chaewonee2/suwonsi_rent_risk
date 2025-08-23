import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🏠 수원시 전세 매물 지도 (클릭 상세보기)")

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_test.csv")

    # ✅ '시', '구' 컬럼이 없으면 '시군구'에서 자동 분리
    if "구" not in df.columns or "시" not in df.columns:
        if "시군구" in df.columns:
            df[["시", "구"]] = df["시군구"].str.split(" ", n=1, expand=True)

    # 전세가율 숫자형 변환
    if "전세가율" in df.columns:
        df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)

    # 위도/경도 결측치 제거
    return df.dropna(subset=["위도", "경도"])

df = load_data()

# --- 지도 생성 ---
col1, col2 = st.columns([2, 1])  # 지도:상세 비율 2:1

with col1:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        si = row.get("시", "")
        gu = row.get("구", "")
        danji = row.get("단지명", "")
        price = row.get("거래금액.만원.", "")
        rent_type = row.get("계약유형", "")
        ratio = row.get("전세가율", "")

        # 클릭했을 때 표시할 정보 (HTML 카드 스타일)
        popup_info = f"""
        <div style="font-size:14px; line-height:1.5;">
            <b style="font-size:16px;">🏢 {danji}</b><br>
            📍 위치: {si} {gu}<br>
            💰 거래금액: <b>{price} 만원</b><br>
            📑 계약유형: {rent_type}<br>
            📊 전세가율: {ratio}%
        </div>
        """

        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=f"{danji} ({price}만원)",  # 마우스 오버
            popup=popup_info                   # 클릭 → 오른쪽에 전달
        ).add_to(marker_cluster)

    st_data = st_folium(m, width=900, height=600)

with col2:
    st.subheader("📋 매물 상세정보")
    if st_data and st_data.get("last_object_clicked_popup"):
        # 클릭한 매물의 상세정보 출력 (HTML 허용)
        st.markdown(st_data["last_object_clicked_popup"], unsafe_allow_html=True)
    else:
        st.info("지도를 클릭하면 상세정보가 여기에 표시됩니다.")
