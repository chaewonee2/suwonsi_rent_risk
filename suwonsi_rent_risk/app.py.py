import streamlit as st
from openai import OpenAI

# OpenAI API Key는 Streamlit Cloud Secrets에 등록해야 합니다
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("🏠 전세사기 위험도 해석 AI (GPT-3.5 Turbo)")

# 사용자 입력: 위험도 점수
risk_score = st.number_input("위험도 점수를 입력하세요 (0~1):", min_value=0.0, max_value=1.0, step=0.01)

if st.button("해석하기"):
    # 사용자 프롬프트 만들기
    user_prompt = f"""
    이 아파트의 전세사기 위험도 점수는 {risk_score:.2f} 입니다.
    - 0.0 ~ 0.3: 안전
    - 0.3 ~ 0.6: 주의
    - 0.6 이상: 위험

    위 점수를 근거로 현재 상황을 해석하고,
    세입자가 어떤 점을 주의해야 할지 3가지 조언을 주세요.
    """

    # GPT-3.5 Turbo 호출
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",   # ✅ 모델 변경 완료
        messages=[
            {"role": "system", "content": "너는 전세사기 위험도를 해석해주는 부동산 AI 컨설턴트야."},
            {"role": "user", "content": user_prompt}
        ]
    )

    # 결과 출력
    st.subheader("📋 AI 해설 결과")
    st.write(response.choices[0].message.content)

