import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# --- 페이지 설정 ---
st.set_page_config(layout="wide", page_title="전세사기 위험 분석", page_icon="🚨")

# --- 데이터 로드 ---
houses = pd.read_csv("fraud_house_location.csv")
population = pd.read_csv("population_by_dong_2021_2024.csv")
safety = pd.read_csv("safety_grade_2021_2024.csv")

# 🔹 population 데이터 전처리 (wide → long)
population = population.melt(
    id_vars=["구", "동"], 
    var_name="year", 
    value_name="population"
)
population["year"] = population["year"].astype(int)

# 🔹 safety 데이터도 혹시 wide라면 같은 방식 처리
if "year" not in safety.columns:
    safety = safety.melt(
        id_vars=["구", "동"], 
        var_name="year", 
        value_name="safety_score"
    )
    safety["year"] = safety["year"].astype(int)

# --- 사이드바 ---
st.sidebar.title("🏠 전세사기 위험 대시보드")
year = st.sidebar.selectbox("연도 선택", sorted(population["year"].unique()))
theme = st.sidebar.selectbox("색상 테마", ["Blues", "Reds", "Viridis"])

# 데이터 필터링
pop_filtered = population[population["year"] == year]
safety_filtered = safety[safety["year"] == year]

# --- 레이아웃: 3컬럼 ---
col1, col2, col3 = st.columns([1, 2, 1])

# --- 컬럼1: 요약 ---
with col1:
    st.subheader("📊 주요 지표")
    st.metric("총 매물 수", len(houses))
    if "risk_score" in houses.columns:
        st.metric("평균 위험도", f"{houses['risk_score'].mean():.2f}")
        st.metric("고위험 매물 수", len(houses[houses["risk_score"] > 0.8]))
    else:
        st.warning("⚠️ houses 데이터에 'risk_score' 컬럼이 없습니다.")

    st.subheader("👥 인구 TOP5")
    st.write(
        pop_filtered.groupby("동")["population"].sum()
        .sort_values(ascending=False).head(5)
    )

# --- 컬럼2: 지도 + 히스토그램 ---
with col2:
    st.subheader("🗺️ 위험 지도")
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12)
    if {"lat", "lon"}.issubset(houses.columns):
        for _, row in houses.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color="red" if row.get("risk_score", 0) > 0.7 else "orange",
                fill=True, fill_opacity=0.6,
                popup=f"{row.get('apt_name', '알수없음')} | 위험도 {row.get('risk_score', 'N/A')}"
            ).add_to(m)
    else:
        st.error("⚠️ houses 데이터에 lat/lon 컬럼이 없습니다.")
    st_folium(m, width=750, height=500)

    if "risk_score" in houses.columns:
        st.subheader("📈 위험 분포 히스토그램")
        fig = px.histogram(
            houses, x="risk_score", nbins=20, color_discrete_sequence=["#ff6b6b"]
        )
        st.plotly_chart(fig, use_container_width=True)

# --- 컬럼3: 랭킹 + 안전지수 ---
with col3:
    if "risk_score" in houses.columns and "gu" in houses.columns:
        st.subheader("🏆 구별 위험도 랭킹")
        gu_rank = houses.groupby("gu")["risk_score"].mean()\
            .sort_values(ascending=False).reset_index()
        st.table(gu_rank.head(10))

    if "safety_score" in safety_filtered.columns:
        st.subheader("🛡️ 안전 지수 TOP5")
        st.write(
            safety_filtered.groupby("구")["safety_score"].mean()
            .sort_values(ascending=False).head(5)
        )
