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

# 2. 지도 출력 및 클릭 정보 받기
clicked = st_folium(m, height=500)

# 3. 클릭한 지점이 있는 경우만 실행
if clicked and clicked["last_clicked"]:
    lat = clicked["last_clicked"]["lat"]
    lon = clicked["last_clicked"]["lng"]

    st.success(f"✅ 선택한 위치: 위도 **{lat:.5f}**, 경도 **{lon:.5f}**")

    # 4. SVF, GVI, BVI 예측 함수 (AI 모델로 교체 가능)
    def predict_svf(lat, lon): return np.clip(0.3 + 0.1 * np.sin(lat + lon), 0, 1)
    def predict_gvi(lat, lon): return np.clip(0.4 + 0.1 * np.cos(lat), 0, 1)
    def predict_bvi(lat, lon): return np.clip(0.3 + 0.08 * np.sin(lon), 0, 1)

    svf = predict_svf(lat, lon)
    gvi = predict_gvi(lat, lon)
    bvi = predict_bvi(lat, lon)

    # 5. 실시간 날씨 정보 (OpenWeatherMap API 사용)
    api_key = "52a4d03e09142c6430952659efda6486"  # 사용자님의 API 키
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        res = requests.get(url)
        weather = res.json()

        temperature = weather["main"]["temp"]
        humidity = weather["main"]["humidity"]
        wind_speed = weather["wind"]["speed"]

        # 6. PET 예측 함수 (임시 수식, 모델 대체 가능)
        def predict_pet(svf, gvi, bvi, temp, hum, wind):
            return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

        pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

        # 7. 결과 출력 (모바일 대응 포함)
        st.markdown("### 📊 예측 결과")
        st.markdown(f"""
        **🗺 위치 정보**  
        - 위도: `{lat:.5f}`  
        - 경도: `{lon:.5f}`

        **🌿 시각 환경 지표 (AI 예측)**  
        - SVF: `{svf:.3f}`  
        - GVI: `{gvi:.3f}`  
        - BVI: `{bvi:.3f}`

        **🌡 실시간 기상 정보**  
        - 기온: `{temperature:.1f} ℃`  
        - 습도: `{humidity:.1f} %`  
        - 풍속: `{wind_speed:.1f} m/s`

        **🔥 예측 체감온도 (PET)**  
        - PET: `{pet:.2f} ℃`
        """)

    except Exception as e:
        st.error("❌ 실시간 날씨 정보를 가져오지 못했습니다. API 키 또는 네트워크를 확인하세요.")
else:
    st.info("🖱 지도에서 예측할 위치를 클릭해주세요.")
