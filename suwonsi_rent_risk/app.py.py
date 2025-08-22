# --- 라이브러리 임포트 ---
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_test.csv")
    df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce")
    df["건축년도"] = pd.to_numeric(df["건축년도"], errors="coerce")
    df = df.dropna(subset=["위도", "경도"])  
    return df

df = load_data()

# --- 지도 생성 ---
st.title("🏠 수원시 전세 매물 지도")

m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
marker_cluster = MarkerCluster().add_to(m)

# 마커 추가 (툴팁으로 표시)
for _, row in df.iterrows():
    tooltip_info = f"""
    📍 {row['단지명']}  
    🏗 건축년도: {int(row['건축년도']) if not pd.isna(row['건축년도']) else '정보 없음'}  
    💰 전세가율: {row['전세가율']}%
    """
    folium.Marker(
        location=[row["위도"], row["경도"]],
        tooltip=tooltip_info  # 마우스 올리면 바로 보임
    ).add_to(marker_cluster)

# --- Streamlit에 지도 표시 ---
st_data = st_folium(m, width=800, height=600)

