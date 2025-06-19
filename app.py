import streamlit as st
import requests
import pydeck as pdk
import pandas as pd
import numpy as np

st.set_page_config(layout="centered")
st.title("🌡️ 위치 기반 PET 예측 시스템")

# 1. 기본 위치 설정 (부산대학교)
default_lat = 35.2325
default_lon = 129.0840

# 2. 지도 클릭 입력 (간단한 위치 입력 폼)
st.markdown("지도를 클릭하거나 위경도를 입력하세요.")

lat = st.number_input("위도 (latitude)", value=default_lat, format="%.6f")
lon = st.number_input("경도 (longitude)", value=default_lon, format="%.6f")

# 3. SVF, GVI, BVI 예측 함수 (실제 모델로 교체 가능)
def predict_svf(lat, lon):
    return np.clip(0.3 + 0.1 * np.sin(lat + lon), 0, 1)

def predict_gvi(lat, lon):
    return np.clip(0.4 + 0.05 * np.cos(lat), 0, 1)

def predict_bvi(lat, lon):
    return np.clip(0.2 + 0.08 * np.sin(lon), 0, 1)

# 4. 실시간 기상 데이터 가져오기 (OpenWeatherMap API 사용)
def get_weather_data(lat, lon):
    api_key = "YOUR_API_KEY"  # 🔑 사용자 API 키 필요
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        return data["main"]["temp"], data["main"]["humidity"], data["wind"]["speed"]
    except:
        st.error("❌ 실시간 기상 데이터를 불러오지 못했습니다. 고정값을 사용합니다.")
        return 27.0, 60, 2.0

# 5. PET 예측 함수 (간단한 수식 기반, 실제 모델로 교체 가능)
def predict_pet(svf, gvi, bvi, temp, humidity, wind_speed):
    return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind_speed * 0.5 + humidity * 0.03

# 6. 버튼 클릭 시 실행
if st.button("📍 위치 기반 PET 예측 실행"):
    svf = predict_svf(lat, lon)
    gvi = predict_gvi(lat, lon)
    bvi = predict_bvi(lat, lon)

    temperature, humidity, wind_speed = get_weather_data(lat, lon)

    pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

    # 7. 결과 출력
    st.markdown("## ✅ 예측 결과")
    st.markdown(f"""
    **🗺️ 위치 정보**
    - 위도: `{lat:.5f}`
    - 경도: `{lon:.5f}`

    **🌡️ 실시간 기상 정보**
    - 기온: `{temperature:.1f} ℃`
    - 습도: `{humidity:.1f} %`
    - 풍속: `{wind_speed:.1f} m/s`

    **🌿 시각 환경 예측**
    - SVF: `{svf:.3f}`
    - GVI: `{gvi:.3f}`
    - BVI: `{bvi:.3f}`

    **🔥 PET 예측값**
    - 체감온도(PET): `{pet:.2f} ℃`
    """)

    # 지도 시각화 (선택)
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=16),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                get_position='[lon, lat]',
                get_color='[255, 0, 0, 160]',
                get_radius=20,
            )
        ]
    ))
