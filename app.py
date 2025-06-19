import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import numpy as np

st.set_page_config(layout="centered")
st.title("🌿 부산대학교 위치 기반 PET 예측 시스템")

# 1. 지도 생성 (부산대학교 중심)
m = folium.Map(location=[35.2325, 129.0840], zoom_start=17)
st.markdown("지도를 클릭해 예측할 위치를 선택하세요.")
clicked = st_folium(m, height=500)

# 2. 클릭된 위치가 있을 경우 처리
if clicked and clicked["last_clicked"]:
    lat = clicked["last_clicked"]["lat"]
    lon = clicked["last_clicked"]["lng"]

    st.markdown(f"✅ 선택한 위치: 위도 **{lat:.5f}**, 경도 **{lon:.5f}**")

    # 3. SVF, GVI, BVI 예측 함수 (임시 수식, AI 모델로 교체 가능)
    def predict_svf(lat, lon): return np.clip(0.3 + 0.1 * np.sin(lat + lon), 0, 1)
    def predict_gvi(lat, lon): return np.clip(0.4 + 0.05 * np.cos(lat), 0, 1)
    def predict_bvi(lat, lon): return np.clip(0.3 + 0.08 * np.sin(lon), 0, 1)

    svf = predict_svf(lat, lon)
    gvi = predict_gvi(lat, lon)
    bvi = predict_bvi(lat, lon)

    # 4. OpenWeatherMap API로 실시간 기온, 습도, 풍속 가져오기
    api_key = "52a4d03e09142c6430952659efda6486"  # 사용자님의 실제 API 키
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        res = requests.get(url)
        weather = res.json()

        temperature = weather["main"]["temp"]
        humidity = weather["main"]["humidity"]
        wind_speed = weather["wind"]["speed"]

        # 5. PET 예측 함수 (간단 수식, 모델 대체 가능)
        def predict_pet(svf, gvi, bvi, temp, hum, wind):
            return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

        pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

        # 6. 결과 출력 (모바일 대응 최적화)
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
        st.error("❌ 실시간 기상 데이터를 가져오지 못했습니다. API 키 또는 네트워크를 확인하세요.")
else:
    st.info("🖱 지도에서 예측하고 싶은 위치를 클릭하세요.")
