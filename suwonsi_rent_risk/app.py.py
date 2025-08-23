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

    # '시', '구' 자동 분리 (없으면 생성)
    if "구" not in df.columns or "시" not in df.columns:
        if "시군구" in df.columns:
            df[["시", "구"]] = df["시군구"].str.split(" ", n=1, expand=True)

    # 전세가율 숫자형 변환
    if "전세가율" in df.columns:
        df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)

    return df.dropna(subset=["위도", "경도"])

df = load_data()

# ----------------
# 지도 + 정보 패널
# ----------------
col1, col2 = st.columns([2, 1])

with col1:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    # 매물마다 고유 key 생성 (단지명 + 층)
    for i, row in df.iterrows():
        unique_key = f"{row['단지명']}_{row['층']}"
        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=f"{row['단지명']} ({row['전세가율']}%)",
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
            row = row_match.iloc[0]

            # 매물정보 카드 출력
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:12px; padding:15px;
                        background:#fff; line-height:1.6;">
                <h4>🏢 {row['단지명']}</h4>
                📍 위치: {row['시']} {row['구']}<br>
                🏗 <b>건축년도:</b> {row['건축년도']}<br>
                🏠 <b>주택유형:</b> {row['주택유형']}<br>
                📊 <b>전세가율:</b> {row['전세가율']}%<br>
                📑 <b>계약유형:</b> {row['계약유형']}<br>
                💰 <b>거래금액:</b> {row['거래금액.만원.']} 만원<br>
                💵 <b>보증금:</b> {row['보증금.만원.']} 만원<br>
                🛗 <b>층:</b> {row['층']}층
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
    else:
        st.info("지도를 클릭하면 매물 정보가 표시됩니다.")

    # ----------------
    # 지역정보 카드 (레이아웃만)
    # ----------------
    st.subheader("🌍 지역정보")
    st.markdown("""
    <div style="border:1px solid #ddd; border-radius:12px; padding:15px;
                background:#f9f9f9; color:#999; line-height:1.6;">
        👉 여기에 나중에 지역정보가 표시될 예정입니다.
    </div>
    """, unsafe_allow_html=True)
