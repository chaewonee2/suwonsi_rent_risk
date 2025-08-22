# --- 1. 라이브러리 임포트 ---
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import openai
import plotly.express as px

# ✅ OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- 2. 페이지 설정 ---
st.set_page_config(
    layout="wide",
    page_title="🏠 수원시 전세사기 위험 매물 분석",
    page_icon="🚨"
)

# --- 3. CSS (프리미엄 스타일) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }

    .premium-header {
        background: linear-gradient(135deg, #ff6b6b, #feca57);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .premium-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    .premium-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.12);
    }

    .metric-box {
        text-align: center;
        padding: 1.2rem;
    }
    .metric-number {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg,#ff6b6b,#feca57);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 데이터 로드 ---
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_15.csv")
    df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce")
    df["보증금.만원."] = pd.to_numeric(df["보증금.만원."], errors="coerce")
    df = df.dropna(subset=["위도", "경도"])
    df["위도_6"] = df["위도"].round(6)
    df["경도_6"] = df["경도"].round(6)
    return df

df = load_data()

# --- 5. 헤더 ---
st.markdown("""
<div class="premium-header">
    <h1>🚨 수원시 전세사기 위험 매물 분석</h1>
    <p>AI 기반 데이터 분석과 GPT 리포트로 전세사기 위험을 한눈에 확인하세요.</p>
</div>
""", unsafe_allow_html=True)

# --- 6. 탭 구성 ---
tab_report, tab_map = st.tabs(["📊 종합 리포트", "🗺️ 위험 매물 지도 & GPT 분석"])

# 📊 종합 리포트
with tab_report:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("📊 주요 지표 요약")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{len(df)}</div>
            <div class="metric-label">총 매물 수</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{df['전세가율'].mean():.2f}%</div>
            <div class="metric-label">평균 전세가율</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{df['전세가율'].max():.2f}%</div>
            <div class="metric-label">최고 전세가율</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 전세가율 분포")
    fig = px.histogram(
        df, x="전세가율", nbins=30,
        title="전세가율 분포 히스토그램",
        labels={"전세가율": "전세가율 (%)"},
        color_discrete_sequence=["#ff6b6b"]
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 🗺️ 지도 + GPT 분석
with tab_map:
    col1, col2 = st.columns([2, 1])

    # 지도
    with col1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.subheader("🗺️ 수원시 전세사기 위험 매물 지도")

        m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
        marker_cluster = MarkerCluster().add_to(m)

        grouped = df.groupby(["위도_6", "경도_6"])
        for (lat, lon), group in grouped:
            if pd.isna(lat) or pd.isna(lon):
                continue
            info = "<br>".join(
                f"<b>{row['단지명']}</b> | 보증금: {row['보증금.만원.']}만원 "
                f"| 전세가율: {row['전세가율']}% | 계약유형: {row['계약유형']}"
                for _, row in group.iterrows()
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color="red",
                fill=True,
                fill_opacity=0.6,
                popup=info
            ).add_to(marker_cluster)

        map_click = st_folium(m, width=750, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

    # GPT 분석 + 매물 리스트 탭
    with col2:
        gpt_tab, table_tab = st.tabs(["🤖 GPT 위험 설명", "📋 매물 리스트"])

        # GPT 위험 설명
        with gpt_tab:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("🤖 GPT 위험 설명")

            if "gpt_cache" not in st.session_state:
                st.session_state["gpt_cache"] = {}

            if map_click and map_click.get("last_object_clicked_popup"):
                popup_text = map_click["last_object_clicked_popup"]
                clicked_name = popup_text.split("<br>")[0].replace("<b>", "").replace("</b>", "").strip()

                if clicked_name not in st.session_state["gpt_cache"]:
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "당신은 부동산 전세사기 위험 분석 전문가입니다."},
                                {"role": "system", "content": "매물 정보를 바탕으로 위험 요인을 두세 문장으로 간단히 설명하세요."},
                                {"role": "user", "content": popup_text.replace("<br>", " ")}
                            ]
                        )
                        gpt_reply = response.choices[0].message.content.strip()
                        st.session_state["gpt_cache"][clicked_name] = gpt_reply
                    except Exception as e:
                        st.session_state["gpt_cache"][clicked_name] = f"❌ GPT 호출 실패: {e}"

                st.markdown(f"### 🏠 선택된 매물: {clicked_name}")
                st.markdown("### 💬 GPT 분석 결과")
                st.write(st.session_state["gpt_cache"][clicked_name])

            else:
                st.info("👉 왼쪽 지도에서 매물을 클릭하세요.")
            st.markdown('</div>', unsafe_allow_html=True)

        # 📋 매물 리스트
        with table_tab:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("📋 전체 매물 리스트")
            st.dataframe(df[["단지명", "보증금.만원.", "전세가율", "계약유형", "위도", "경도"]])
            st.markdown('</div>', unsafe_allow_html=True)
