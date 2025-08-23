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

    # '시', '구' 없으면 자동 분리
    if "구" not in df.columns or "시" not in df.columns:
        if "시군구" in df.columns:
            df[["시", "구"]] = df["시군구"].str.split(" ", n=1, expand=True)

    # 전세가율 숫자형 변환
    if "전세가율" in df.columns:
        df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)

    return df.dropna(subset=["위도", "경도"])

df = load_data()

# --- 지도 + 상세 정보 ---
col1, col2 = st.columns([2, 1])

with col1:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df.iterrows():
        si = row.get("시", "")
        gu = row.get("구", "")
        danji = row.get("단지명", "")
        price = row.get("거래금액.만원.", "")
        rent_type = row.get("계약유형", "")
        ratio = row.get("전세가율", "")
        area = row.get("전용면적", "")
        year = row.get("건축년도", "")
        risk = row.get("위험도점수", "N/A")   # 위험도점수 컬럼 있다고 가정

        # --- 지도 팝업 (정사각형 느낌 카드) ---
        popup_html = f"""
        <div style="
            width:150px; height:80px;
            border:1px solid #888;
            border-radius:8px;
            background:#f9f9f9;
            text-align:center;
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            font-size:13px;
            font-weight:bold;">
            {danji}<br>⚠️ 위험도: {risk}점
        </div>
        """

        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=f"{danji} ({risk}점)",
            popup=popup_html
        ).add_to(marker_cluster)

        # --- 오른쪽 상세 카드 HTML ---
        detail_info = f"""
        <div style="
            border:1px solid #ddd;
            border-radius:12px;
            padding:15px;
            margin-bottom:15px;
            box-shadow:2px 2px 8px rgba(0,0,0,0.1);
            background-color:white;
            font-size:14px;
            line-height:1.6;">
            
            <h3 style="margin:0 0 10px 0;">🏢 {danji}</h3>
            <p>📍 <b>위치:</b> {si} {gu}</p>
            <p>💰 <b>거래금액:</b> {price} 만원</p>
            <p>📑 <b>계약유형:</b> {rent_type}</p>
            <p>📊 <b>전세가율:</b> {ratio}%</p>
            <p>📐 <b>전용면적:</b> {area}㎡</p>
            <p>🏗 <b>건축년도:</b> {year}</p>
            <p>⚠️ <b>위험도점수:</b> {risk}점</p>
        </div>
        """

        df.at[i, "detail_info"] = detail_info

    st_data = st_folium(m, width=900, height=600)

with col2:
    st.subheader("📋 매물 상세정보")
    if st_data and st_data.get("last_object_clicked_popup"):
        clicked_name = st_data["last_object_clicked_popup"]
        row_match = df[df["단지명"] == clicked_name]
        if not row_match.empty:
            st.markdown(row_match.iloc[0]["detail_info"], unsafe_allow_html=True)
    else:
        st.info("지도를 클릭하면 상세정보가 여기에 표시됩니다.")
