import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import numpy as np

# 페이지 설정
st.set_page_config(layout="centered")
st.title("🌿 부산대학교 기반 PET 예측 시스템")
st.markdown("지도를 클릭하면 해당 위치의 SVF, GVI, BVI, 실시간 기상정보, PET를 예측합니다.")

# 1. 지도 설정
center_lat = 35.2325
center_lon = 129.0840
m = folium.Map(location=[center_lat, center_lon], zoom_start=17)
clicked = st_folium(m, height=500)

# 2. 클릭 위치 받아오기 (없으면 기본값)
if clicked and clicked.get("last_clicked"):
    lat = clicked["last_clicked"]["lat"]
    lon = clicked["last_clicked"]["lng"]
    st.success(f"✅ 위치 선택됨: 위도 {lat:.5f}, 경도 {lon:.5f}")
else:
    st.warning("⚠️ 지도를 클릭하지 않았습니다. 기본 위치로 예측합니다.")
    lat = center_lat
    lon = center_lon

# 3. 개선된 수식 기반 SVF/GVI/BVI 예측 함수
def predict_svf(lat, lon):
    return np.clip((np.sin(lat * 10) + np.cos(lon * 10)) * 0.3 + 0.5, 0, 1)

def predict_gvi(lat, lon):
    return np.clip((np.cos(lat * 8) - np.sin(lon * 6)) * 0.25 + 0.5, 0, 1)

def predict_bvi(lat, lon):
    return np.clip(1 - predict_svf(lat, lon) - predict_gvi(lat, lon), 0, 1)

svf = predict_svf(lat, lon)
gvi = predict_gvi(lat, lon)
bvi = predict_bvi(lat, lon)

# 4. 실시간 기상정보 (OpenWeatherMap)
api_key = "52a4d03e09142c6430952659efda6486"  # 본인의 API 키로 대체
weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

try:
    response = requests.get(weather_url)
    weather = response.json()
    temperature = weather["main"]["temp"]
    humidity = weather["main"]["humidity"]
    wind_speed = weather["wind"]["speed"]

    # 5. PET 계산 (간단 수식 기반)
    def predict_pet(svf, gvi, bvi, temp, hum, wind):
        return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

    pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

    # 6. 결과 출력
    st.markdown("### 📊 예측 결과")
    st.markdown(f"""
    **🗺 위치 정보**  
    - 위도: `{lat:.5f}`  
    - 경도: `{lon:.5f}`

    **🌿 시각 환경 예측값**  
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
    st.error("❌ 실시간 날씨 정보를 불러오지 못했습니다.")
    st.code(str(e))
