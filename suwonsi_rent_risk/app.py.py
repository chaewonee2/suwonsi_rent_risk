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
deposit = pd.read_csv("deposit_accidents_202407.csv")
housing = pd.read_csv("housing_status_20250430.csv")
pop_mob = pd.read_csv("pop_mobility_2020_2024.csv")
gond = pd.read_csv("gondgondimdae.csv")

# --- deposit accidents 전처리 ---
if "사고일자" in deposit.columns:
    deposit["사고일자"] = pd.to_datetime(deposit["사고일자"], errors="coerce")

# --- population 데이터 (wide → long) ---
population = population.melt(
    id_vars=["구", "동"], 
    var_name="year", 
    value_name="population"
)
population["year"] = pd.to_numeric(population["year"], errors="coerce")
population = population.dropna(subset=["year"])
population["year"] = population["year"].astype(int)

# --- safety 데이터 (wide → long, 자동 구/동 판단) ---
if "year" not in safety.columns:
    id_vars = []
    if "구" in safety.columns: id_vars.append("구")
    if "동" in safety.columns: id_vars.append("동")

    safety = safety.melt(
        id_vars=id_vars, 
        var_name="year", 
        value_name="safety_score"
    )
    safety["year"] = pd.to_numeric(safety["year"], errors="coerce")
    safety = safety.dropna(subset=["year"])
    safety["year"] = safety["year"].astype(int)

# --- pop_mobility 데이터 (wide → long) ---
if "year" not in pop_mob.columns:
    id_vars = [c for c in pop_mob.columns if c not in ["2020","2021","2022","2023","2024"]]
    pop_mob = pop_mob.melt(
        id_vars=id_vars, var_name="year", value_name="mobility"
    )
    pop_mob["year"] = pd.to_numeric(pop_mob["year"], errors="coerce")
    pop_mob = pop_mob.dropna(subset=["year"])
    pop_mob["year"] = pop_mob["year"].astype(int)

# --- gondgondimdae (wide → long 필요 시) ---
if any(col.isdigit() for col in gond.columns):  # 연도 컬럼이 있으면
    id_vars = [c for c in gond.columns if not c.isdigit()]
    gond = gond.melt(
        id_vars=id_vars, var_name="year", value_name="value"
    )
    gond["year"] = pd.to_numeric(gond["year"], errors="coerce")
    gond = gond.dropna(subset=["year"])
    gond["year"] = gond["year"].astype(int)

# --- 사이드바 ---
st.sidebar.title("🏠 전세사기 위험 대시보드")
year = st.sidebar.selectbox("연도 선택", sorted(population["year"].unique()))
theme = st.sidebar.selectbox("색상 테마", ["Blues", "Reds", "Viridis"])

# --- 데이터 필터링 ---
pop_filtered = population[population["year"] == year]
safety_filtered = safety[safety["year"] == year]

# --- 레이아웃 ---
col1, col2, col3 = st.columns([1, 2, 1])

# 📊 컬럼1: 요약
with col1:
    st.subheader("📊 주요 지표")
    st.metric("총 매물 수", len(houses))
    if "risk_score" in houses.columns:
        st.metric("평균 위험도", f"{houses['risk_score'].mean():.2f}")
        st.metric("고위험 매물 수", len(houses[houses["risk_score"] > 0.8]))
    else:
        st.warning("⚠️ houses 데이터에 'risk_score' 컬럼이 없습니다.")
    st.subheader("👥 인구 TOP5")
    st.write(pop_filtered.groupby("동")["population"].sum().sort_values(ascending=False).head(5))

# 🗺️ 컬럼2: 지도 + 히스토그램
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
                popup=f"{row.get('apt_name','알수없음')} | 위험도 {row.get('risk_score','N/A')}"
            ).add_to(m)
    st_folium(m, width=750, height=500)
    if "risk_score" in houses.columns:
        st.subheader("📈 위험 분포 히스토그램")
        fig = px.histogram(houses, x="risk_score", nbins=20, color_discrete_sequence=["#ff6b6b"])
        st.plotly_chart(fig, use_container_width=True)

# 🏆 컬럼3: 랭킹 + 안전지수
with col3:
    if "risk_score" in houses.columns and "gu" in houses.columns:
        st.subheader("🏆 구별 위험도 랭킹")
        gu_rank = houses.groupby("gu")["risk_score"].mean().sort_values(ascending=False).reset_index()
        st.table(gu_rank.head(10))
    if "safety_score" in safety_filtered.columns:
        st.subheader("🛡️ 안전 지수 TOP5")
        st.write(safety_filtered.groupby("구")["safety_score"].mean().sort_values(ascending=False).head(5))
