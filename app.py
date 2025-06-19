import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import numpy as np

st.set_page_config(layout="centered")
st.title("🌿 부산대학교 위치 기반 PET 예측 시스템")
st.markdown("지도를 클릭해 예측할 위치를 선택하세요.")

# 1. 지도 생성 (부산대학교 중심)
m = folium.Map(location=[35.2325, 129.0840], zoom_start=17)
clicked = st_folium(m, height=500, returned_objects=["last_clicked"])

# 2. 클릭된 위치 디버깅 출력 (모바일 확인용)
st.write("📍 클릭된 위치 데이터:", clicked)

# 3. 위치 결정 (클릭 없으면 기본값)
if clicked and clicked["last_clicked"]:
    lat = clicked["last_clicked"]["lat"]
    lon = clicked["last_clicked"]["lng"]
    clicked_flag = True
else:
    lat = 35.2325
    lon = 129.0840
    clicked_flag = False

# 4. SVF, GVI, BVI 예측 (간단 수식)
def predict_svf(lat, lon): return np.clip(0.3 + 0.1 * np.sin(lat + lon), 0, 1)
def predict_gvi(lat, lon): return np.clip(0.4 + 0.1 * np.cos(lat), 0, 1)
def predict_bvi(lat, lon): return np.clip(0.3 + 0.08 * np.sin(lon), 0, 1)

svf = predict_svf(lat, lon)
gvi = predict_gvi(lat, lon)
bvi = predict_bvi(lat, lon)

# 5. 날씨 정보 가져오기
api_key = "52a4d03e09142c6430952659efda6486"
url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

try:
    res = requests.get(url)
    weather = res.json()

    temperature = weather["main"]["temp"]
    humidity = weather["main"]["humidity"]
    wind_speed = weather["wind"]["speed"]

    # 6. PET 계산 함수
    def predict_pet(svf, gvi, bvi, temp, hum, wind):
        return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

    pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

    # 7. 출력
    if clicked_flag:
        st.success(f"✅ 선택한 위치: 위도 **{lat:.5f}**, 경도 **{lon:.5f}**")
    else:
        st.info("📌 기본 위치(부산대 중심 기준)로 예측된 결과입니다.")

    st.markdown("### 📊 예측 결과")
    st.markdown(f"""
    **🗺 위치**  
    - 위도: `{lat:.5f}`  
    - 경도: `{lon:.5f}`

    **🌿 시각 환경 지표**  
    - SVF: `{svf:.3f}`  
    - GVI: `{gvi:.3f}`  
    - BVI: `{bvi:.3f}`

    **🌡 실시간 기상 정보**  
    - 기온: `{temperature:.1f} ℃`  
    - 습도: `{humidity:.1f} %`  
    - 풍속: `{wind_speed:.1f} m/s`

    **🔥 예측 PET (체감온도)**  
    - PET: `{pet:.2f} ℃`
    """)

except Exception as e:
    st.error("❌ 실시간 날씨 데이터를 불러오지 못했습니다. 네트워크 또는 API 키를 확인하세요.")
