import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

st.set_page_config(layout="wide", page_title="전세사기 위험 분석", page_icon="🚨")

# --- 데이터 로드 ---
houses = pd.read_csv("fraud_house_location.csv")
population = pd.read_csv("population_by_dong_2021_2024.csv")
safety = pd.read_csv("safety_grade_2021_2024.csv")

# --- 사이드바 ---
st.sidebar.title("🏠 전세사기 위험 대시보드")
year = st.sidebar.selectbox("연도 선택", sorted(population["year"].unique()))
theme = st.sidebar.selectbox("색상 테마", ["Blues", "Reds", "Viridis"])

pop_filtered = population[population["year"] == year]
safety_filtered = safety[safety["year"] == year]

# --- 레이아웃: 3컬럼 ---
col1, col2, col3 = st.columns([1, 2, 1])

# --- 컬럼1: 요약 ---
with col1:
    st.subheader("📊 주요 지표")
    st.metric("총 매물 수", len(houses))
    st.metric("평균 위험도", f"{houses['risk_score'].mean():.2f}")
    st.metric("고위험 매물 수", len(houses[houses["risk_score"] > 0.8]))

    st.subheader("👥 인구 현황")
    st.write(pop_filtered.groupby("dong")["population"].sum().sort_values(ascending=False).head(5))

# --- 컬럼2: 지도 + 히트맵 ---
with col2:
    st.subheader("🗺️ 위험 지도")
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12)
    for _, row in houses.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5,
            color="red" if row["risk_score"] > 0.7 else "orange",
            fill=True, fill_opacity=0.6,
            popup=f"{row['apt_name']} | 위험도 {row['risk_score']:.2f}"
        ).add_to(m)
    st_folium(m, width=750, height=500)

    st.subheader("📈 위험 분포 히스토그램")
    fig = px.histogram(houses, x="risk_score", nbins=20, color_discrete_sequence=["#ff6b6b"])
    st.plotly_chart(fig, use_container_width=True)

# --- 컬럼3: 랭킹 + 세부정보 ---
with col3:
    st.subheader("🏆 구별 위험도 랭킹")
    gu_rank = houses.groupby("gu")["risk_score"].mean().sort_values(ascending=False).reset_index()
    st.table(gu_rank.head(10))

    st.subheader("🛡️ 안전 지수")
    st.write(safety_filtered.groupby("gu")["safety_score"].mean().sort_values(ascending=False).head(5))
