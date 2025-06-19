import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import numpy as np

# 앱 초기 설정
st.set_page_config(layout="centered")
st.title("📍 부산대학교 기반 PET 예측 시스템")
st.markdown("지도를 클릭하면 해당 위치의 시각 환경, 기상 정보, PET(체감온도)을 예측합니다.")

# 지도 중심 위치 (부산대)
center_lat = 35.2325
center_lon = 129.0840

# 지도 객체 생성
m = folium.Map(location=[center_lat, center_lon], zoom_start=17)
map_data = st_folium(m, height=500)

# 기본값
lat = None
lon = None

# 지도 클릭 시 좌표 추출
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"✅ 위치 선택됨: 위도 {lat:.5f}, 경도 {lon:.5f}")
else:
    st.warning("⚠️ 지도를 클릭해주세요. (선택 안되면 기본 위치로 예측)")
    lat = center_lat
    lon = center_lon

# SVF, GVI, BVI 예측 함수 (예시)
def predict_svf(lat, lon): return np.clip(0.3 + 0.1 * np.sin(lat + lon), 0, 1)
def predict_gvi(lat, lon): return np.clip(0.4 + 0.05 * np.cos(lat), 0, 1)
def predict_bvi(lat, lon): return np.clip(0.3 + 0.07 * np.sin(lon), 0, 1)

svf = predict_svf(lat, lon)
gvi = predict_gvi(lat, lon)
bvi = predict_bvi(lat, lon)

# OpenWeatherMap API로 실시간 날씨 가져오기
api_key = "52a4d03e09142c6430952659efda6486"
weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

try:
    response = requests.get(weather_url)
    weather = response.json()

    temperature = weather["main"]["temp"]
    humidity = weather["main"]["humidity"]
    wind_speed = weather["wind"]["speed"]

    # PET 계산 함수 (예시 모델)
    def predict_pet(svf, gvi, bvi, temp, hum, wind):
        return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

    pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

    # 결과 출력
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

    **🔥 PET 예측 (체감온도)**  
    - PET: `{pet:.2f} ℃`
    """)

except Exception as e:
    st.error("❌ 실시간 날씨 데이터를 불러오는 데 실패했습니다.")
    st.code(str(e))
