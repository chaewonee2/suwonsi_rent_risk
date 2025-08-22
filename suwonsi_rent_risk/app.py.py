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
    df["전세가율"] = pd.to_numeric(df["전세가율"], errors="coerce").round(0)
    return df.dropna(subset=["위도","경도"])

df = load_data()

# --- 지도 생성 ---
col1, col2 = st.columns([2, 1])  # 지도:상세 비율 2:1

with col1:
    m = folium.Map(location=[37.2636, 127.0286], zoom_start=12, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        tooltip_info = f"{row['단지명']} | 전세가율 {row['전세가율']}%"
        popup_info = row["단지명"]
        
        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=tooltip_info,
            popup=popup_info
        ).add_to(marker_cluster)

    map_click = st_folium(m, width=800, height=600)

with col2:
    st.subheader("🏠 선택된 매물 정보")

    if map_click and map_click.get("last_object_clicked_popup"):
        selected_name = map_click["last_object_clicked_popup"]
        row = df[df["단지명"] == selected_name].iloc[0]

        # 카드 스타일 적용
        st.markdown(
            f"""
            <div style="background: #fff8f0; padding: 1.5rem; border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h3 style="margin-top:0; color:#d35400;">{row['단지명']}</h3>
                <p><b>건축년도:</b> {int(row['건축년도']) if not pd.isna(row['건축년도']) else '정보 없음'}</p>
                <p><b>주택유형:</b> {row['주택유형']}</p>
                <p><b>전세가율:</b> {row['전세가율']}%</p>
                <p><b>임대구분:</b> {row['임대구분']}</p>
                <p><b>주택인허가:</b> {row['주택인허가_단순']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("👉 지도에서 매물을 클릭하세요.")

