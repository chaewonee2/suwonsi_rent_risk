import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🏠 수원시 전세 매물 위험 탐지")

# ----------------
# 데이터 불러오기
# ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_19_ex.csv")  # ⚠️ 파일명 실행환경에 맞게 수정

    # 시군구 → 시, 구 분리
    if "구" not in df.columns or "시" not in df.columns:
        if "시군구" in df.columns:
            df[["시", "구"]] = df["시군구"].str.split(" ", n=1, expand=True)

    # 전세가율 숫자 변환
    if "전세가율" in df.columns:
        df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)

    return df.dropna(subset=["위도", "경도"])

df = load_data()

# ----------------
# 3열 레이아웃
# ----------------
col_left, col_mid, col_right = st.columns([0.8, 2.8, 0.8], gap="small")

# ----------------
# 지역정보 (왼쪽)
# ----------------
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

# ----------------
# 지도 (가운데)
# ----------------
with col_mid:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df.iterrows():
        unique_key = f"{row['단지명']}_{row['층']}"
        df.at[i, "unique_key"] = unique_key

        # 위험점수 (% 값 그대로 사용)
        위험점수 = round(row["위험확률"], 1)

        # 위험등급 색상 매핑
        if row["위험등급"] == "안전":
            bg_color = "#d4f7d4"
        elif row["위험등급"] == "주의":
            bg_color = "#fff3b0"
        elif row["위험등급"] == "위험":
            bg_color = "#ffcc99"
        else:
            bg_color = "#f0f0f0"

        # 툴팁 (hover)
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

        # 팝업 (click)
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

# ----------------
# 매물정보 (오른쪽)
# ----------------
row = None
with col_right:
    st.subheader("📋 매물 상세정보")

    if st_data and st_data.get("last_object_clicked_popup"):
        clicked_popup = st_data["last_object_clicked_popup"]

        # popup_html 안에서 unique_key 추출
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

            # 위험등급 색상 매핑
            if row["위험등급"] == "안전":
                card_color = "#d4f7d4"
            elif row["위험등급"] == "주의":
                card_color = "#fff3b0"
            elif row["위험등급"] == "위험":
                card_color = "#ffcc99"
            else:
                card_color = "#ffffff"

            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:12px; padding:20px;
                        background:{card_color}; line-height:1.6; min-height:600px;">
                <h4>🏢 {row['단지명']}</h4>
                <h5>🚦 위험등급: {row['위험등급']}</h5>
                <h5>⚠️ 위험점수: {위험점수}점</h5>
                <h5>📊 전세가율: {row['전세가율']}</h5>
                📍 위치: {row['시']} {row['구']}<br>
                🏗 건축년도: {row['건축년도']}<br>
                🏠 주택유형: {row['주택유형']}<br>
                🏠 임대구분: {row['임대구분']}<br>
                📑 계약유형: {row['계약유형']}<br>
                📑 주택인허가 : {row['주택인허가_단순']}<br>
                💰 거래금액: {row['거래금액.만원.']} 만원<br>
                💵 보증금: {row['보증금.만원.']} 만원<br>
                🏠 전용면적: {row['전용면적']}<br>
                🛗 층: {row['층']}층<br>
            </div>
            """, unsafe_allow_html=True)

            # ----------------
            # GPT 설명 카드 (새로운 카드로 추가)
            # ----------------
            gpt_text = f"""
            <div style="border:1px solid #ddd; border-radius:12px; padding:20px;
                        background:#fdf6e3; line-height:1.6; margin-top:20px;">
                <h4>🤖 전세사기 컨설턴트 조언</h4>
                <p>이 매물에서 특히 주의해야 할 위험 신호 3가지를 말씀드릴게요.<br>
                데이터 분석 결과 ‘안전’보다는 한 단계 낮은 <b>주의 등급</b>에 속합니다.<br>
                즉, 아직은 심각한 위험은 아니지만, 문제가 발생할 가능성이 열려있다는 뜻이에요.</p>

                <p><b>건축년도 ({row['건축년도']}년)</b><br>
                오래된 아파트라 관리비 체납, 집주인의 유지·보수 부담이 클 수 있습니다.<br>
                이런 경우 전세금을 돌려받지 못하는 사례가 상대적으로 많습니다.</p>

                <p><b>보증금 규모 ({row['보증금.만원.']} 만원)</b><br>
                보증금이 크기 때문에 집주인 문제 발생 시 피해액이 커질 수 있습니다.<br>
                최근 보증금이 높은 구축 아파트에서 사기가 다수 보고된 점도 주의해야 합니다.</p>

                <h5>✅ 세입자가 해야 할 일 3가지</h5>
                <ul>
                    <li>등기부등본 확인 → 근저당, 가압류 여부 체크</li>
                    <li>전입 + 확정일자 → 계약 직후 반드시 처리</li>
                    <li>보증보험 가입 → HUG, SGI 가입 가능 여부 확인</li>
                </ul>

                <h5>📄 필요한 서류 & 확인 포인트</h5>
                <ul>
                    <li>등기부등본: 근저당, 가압류, 소유권 변동 기록 확인</li>
                    <li>건축물대장: 실제 용도와 일치하는지 확인</li>
                    <li>전입신고 & 확정일자: 동사무소 / 정부24 처리 가능</li>
                    <li>보증보험: 신청 마감 시간(대개 오후 4시 이전) 전 처리</li>
                </ul>

                <p><b>정리</b>하자면, 이 매물은 조건은 나쁘지 않지만 
                <b>구축 + 주의등급 + 보증금 규모</b>라는 점에서 꼭 조심하셔야 합니다.<br>
                특히 오늘 말씀드린 3가지 절차만 지켜도 피해 위험을 크게 줄일 수 있으니, 
                꼭 확인하시고 진행하시길 권장드립니다.</p>
            </div>
            """
            st.markdown(gpt_text, unsafe_allow_html=True)

        else:
            st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
    else:
        st.info("지도를 클릭하면 매물 정보가 표시됩니다.")
