import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from openai import OpenAI

st.set_page_config(layout="wide")
st.title("🏠 수원시 전세사기 위험도 분석 AI (GPT-3.5 Turbo)")

# -----------------------
# 1. 데이터 불러오기
# -----------------------
houses = pd.read_csv("fraud_house_location.csv")  # lat, lon, apt_name, gu, risk_score 포함
pop = pd.read_csv("population_by_dong_2021_2024.csv")  # 구/동별 인구 (2021~2024)
safety = pd.read_csv("safety_grade_2021_2024.csv")  # 구별 안전등급 데이터

# 최신 연도 데이터만 사용 (예: 2024년)
pop_latest = pop[pop["year"] == 2024].groupby("gu")["population"].sum().reset_index()
safety_latest = safety[safety["year"] == 2024].groupby("gu")["safety_score"].mean().reset_index()

# 구별 평균 위험도
gu_mean = houses.groupby("gu")["risk_score"].mean().reset_index()

# -----------------------
# 2. 지도 표시
# -----------------------
m = folium.Map(location=[37.2636, 127.0286], zoom_start=12)  # 수원 중심 좌표
for idx, row in houses.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"{row['apt_name']} ({row['gu']})",
        tooltip=f"{row['apt_name']} - 위험도 {row['risk_score']:.2f}"
    ).add_to(m)

map_data = st_folium(m, width=900, height=600)

# -----------------------
# 3. 마커 클릭 이벤트
# -----------------------
if map_data["last_object_clicked"]:
    lat, lon = map_data["last_object_clicked"]["lat"], map_data["last_object_clicked"]["lng"]
    selected_house = houses[(houses["lat"] == lat) & (houses["lon"] == lon)].iloc[0]

    # 선택된 주택 기본 정보
    st.subheader("🏢 선택된 주택 정보")
    st.write(f"- 단지명: {selected_house['apt_name']}")
    st.write(f"- 구: {selected_house['gu']}")
    st.write(f"- 위험도 점수: {selected_house['risk_score']:.2f}")

    # 구별 평균 위험도
    gu_avg = gu_mean.loc[gu_mean["gu"] == selected_house["gu"], "risk_score"].values[0]
    st.write(f"- {selected_house['gu']} 평균 위험도: {gu_avg:.2f}")

    # 구별 인구
    gu_pop = pop_latest.loc[pop_latest["gu"] == selected_house["gu"], "population"].values[0]
    st.write(f"- {selected_house['gu']} 인구: {gu_pop:,} 명")

    # 구별 안전지수
    gu_safety = safety_latest.loc[safety_latest["gu"] == selected_house["gu"], "safety_score"].values[0]
    st.write(f"- {selected_house['gu']} 안전지수: {gu_safety:.2f}")

    # -----------------------
    # 4. GPT 해석
    # -----------------------
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    user_prompt = f"""
    선택된 아파트 정보:
    - 단지명: {selected_house['apt_name']}
    - 위치: {selected_house['gu']}
    - 위험도 점수: {selected_house['risk_score']:.2f}
    - 해당 구 평균 위험도: {gu_avg:.2f}
    - 해당 구 인구: {gu_pop:,} 명
    - 해당 구 안전지수: {gu_safety:.2f}

    위 데이터를 근거로,
    1) 위험도가 구 평균 대비 어떤 수준인지 설명하고,
    2) 인구 규모와 안전지수를 고려한 해석을 덧붙이고,
    3) 세입자가 주의해야 할 점 3가지,
    4) 관련 법적/행정적 조언,
    5) 구별 특성을 반영한 추가 분석
    을 해줘.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",   # ✅ GPT-3.5 Turbo 사용
        messages=[
            {"role": "system", "content": "너는 전세사기 위험도를 해석해주는 부동산 AI 컨설턴트야."},
            {"role": "user", "content": user_prompt}
        ]
    )

    st.subheader("📋 AI 해설 결과")
    st.write(response.choices[0].message.content)

