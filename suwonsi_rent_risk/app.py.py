import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🏠 수원시 전세 매물 지도 (클릭 상세보기)")

# ----------------
# 데이터 불러오기
# ----------------
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

# ----------------
# 3열 레이아웃 (지도 넓게, 여백 최소화)
# ----------------
col_left, col_mid, col_right = st.columns([0.8, 2.8, 0.8], gap="small")

# 지역정보 (왼쪽)
with col_left:
    st.subheader("🌍 지역정보")
    selected_gu = st.radio(
        "행정구 선택:",
        ["권선구", "장안구", "영통구", "팔달구"]
    )

    st.markdown(f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:15px;
                background:#fff; line-height:1.6; min-height:400px;">
        <h4>🏙️ {selected_gu}</h4>
        👉 여기에 {selected_gu} 지역정보가 표시될 예정입니다.
    </div>
    """, unsafe_allow_html=True)

# 지도 (가운데 → 넓게)
with col_mid:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df.iterrows():
        unique_key = f"{row['단지명']}_{row['층']}"
        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=f"{row['단지명']} ({row['전세가율']}%)",
            popup=unique_key
        ).add_to(marker_cluster)
        df.at[i, "unique_key"] = unique_key

    st_data = st_folium(m, width=900, height=650)  # 지도 더 크게

# 매물정보 (오른쪽)
with col_right:
    st.subheader("📋 매물 상세정보")

    if st_data and st_data.get("last_object_clicked_popup"):
        clicked_key = st_data["last_object_clicked_popup"]
        row_match = df[df["unique_key"] == clicked_key]

        if not row_match.empty:
            row = row_match.iloc[0]
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:12px; padding:15px;
                        background:#fff; line-height:1.6; min-height:400px;">
                <h4>🏢 {row['단지명']}</h4>
                📍 위치: {row['시']} {row['구']}<br>
                🏗 건축년도: {row['건축년도']}<br>
                🏠 주택유형: {row['주택유형']}<br>
                📊 전세가율: {row['전세가율']}%<br>
                📑 계약유형: {row['계약유형']}<br>
                💰 거래금액: {row['거래금액.만원.']} 만원<br>
                💵 보증금: {row['보증금.만원.']} 만원<br>
                🛗 층: {row['층']}층
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
    else:
        st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
