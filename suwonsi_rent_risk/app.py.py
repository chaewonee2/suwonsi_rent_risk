import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import openai

st.set_page_config(layout="wide")
st.title("🏠 수원시 전세 매물 위험 탐지")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ----------------
# 데이터 불러오기
# ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_19_ex.csv")

    # 시군구 → 시, 구 분리
    if "구" not in df.columns or "시" not in df.columns:
        if "시군구" in df.columns:
            df[["시", "구"]] = df["시군구"].str.split(" ", n=1, expand=True)

    if "전세가율" in df.columns:
        df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)

    return df.dropna(subset=["위도", "경도"])

df = load_data()

# ----------------
# 3열 레이아웃
# ----------------
col_left, col_mid, col_right = st.columns([0.8, 2.8, 1], gap="small")

# 🌍 지역정보 (왼쪽)
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

# 🗺️ 지도 (가운데)
with col_mid:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df.iterrows():
        unique_key = f"{row['단지명']}_{row['층']}"
        df.at[i, "unique_key"] = unique_key

        위험점수 = round(row["위험확률"], 1)

        # 색상 매핑
        if row["위험등급"] == "안전":
            bg_color = "#d4f7d4"
        elif row["위험등급"] == "주의":
            bg_color = "#fff3b0"
        elif row["위험등급"] == "위험":
            bg_color = "#ffcc99"
        else:
            bg_color = "#f0f0f0"

        tooltip_html = f"""
        <div style="font-size:13px; line-height:1.6; 
                    border:1px solid #ccc; border-radius:8px; 
                    background-color:{bg_color}; padding:6px 10px;">
            <b>단지명:</b> {row['단지명']}<br>
            <b>주택유형:</b> {row['주택유형']}<br>
            <b>위험등급:</b> {row['위험등급']}<br>
            <b>위험점수:</b> {위험점수}점
        </div>
        """

        popup_html = f"""
        <div style="font-size:14px; line-height:1.8; 
                    border:1px solid #444; border-radius:10px; 
                    background-color:#f9f9f9; padding:10px 14px;">
            <b>단지명:</b> {row['단지명']}<br>
            <b>주택유형:</b> {row['주택유형']}<br>
            {unique_key}
        </div>
        """

        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(marker_cluster)

    st_data = st_folium(m, width=900, height=650)

# 📋 매물정보 (오른쪽 + GPT 분석)
with col_right:
    st.subheader("📋 매물 상세정보")

    if st_data and st_data.get("last_object_clicked_popup"):
        clicked_popup = st_data["last_object_clicked_popup"]

        clicked_key = None
        for key in df["unique_key"]:
            if key in clicked_popup:
                clicked_key = key
                break

        if clicked_key:
            row_match = df[df["unique_key"] == clicked_key]
        else:
            row_match = pd.DataFrame()

        if not row_match.empty:
            row = row_match.iloc[0]
            위험점수 = round(row["위험확률"], 1)

            # 🟡 상세정보 + GPT 카드
            prompt = f"""
            단지명: {row['단지명']}
            위험등급: {row['위험등급']}
            위험점수: {위험점수}
            전세가율: {row['전세가율']}%
            건축년도: {row['건축년도']}
            주택유형: {row['주택유형']}
            계약유형: {row['계약유형']}
            보증금: {row['보증금.만원.']} 만원
            거래금액: {row['거래금액.만원.']} 만원

            위 데이터를 바탕으로 전세사기 위험 가능성을 설명하고,
            계약 시 유의사항이나 예방 조언을 시민 눈높이에 맞춰 3~5문장으로 작성해줘.
            """

            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "너는 전세사기 컨설턴트다. 시민 눈높이에 맞춰 설명과 실질적인 조언을 제공해라."},
                        {"role": "user", "content": prompt}
                    ]
                )
                gpt_reply = response.choices[0].message.content
            except Exception as e:
                gpt_reply = f"❌ GPT 분석 실패: {e}"

            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:12px; padding:25px;
                        background:#fff8e1; line-height:1.6; min-height:700px;">
                <h4>🏢 {row['단지명']}</h4>
                <p><b>🚦 위험등급:</b> {row['위험등급']}</p>
                <p><b>⚠️ 위험점수:</b> {위험점수}점</p>
                <p><b>📊 전세가율:</b> {row['전세가율']}%</p>
                <p><b>🏗 건축년도:</b> {row['건축년도']}</p>
                <p><b>🏠 주택유형:</b> {row['주택유형']}</p>
                <p><b>🏠 임대구분:</b> {row['임대구분']}</p>
                <p><b>📑 계약유형:</b> {row['계약유형']}</p>
                <p><b>📑 주택인허가:</b> {row['주택인허가_단순']}</p>
                <p><b>💵 보증금:</b> {row['보증금.만원.']} 만원</p>
                <p><b>💰 거래금액:</b> {row['거래금액.만원.']} 만원</p>
                <p><b>📐 전용면적:</b> {row['전용면적']}</p>
                <p><b>🛗 층:</b> {row['층']}층</p>

                <hr>
                <h4>💬 전세사기 컨설턴트 조언</h4>
                <p>{gpt_reply}</p>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
    else:
        st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
