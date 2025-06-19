import streamlit as st
import pandas as pd
import numpy as np

# 예시용 함수 (실제 모델로 교체 가능)
def predict_svf(lat, lon):
    return np.clip(0.3 + 0.1 * np.sin(lat + lon), 0, 1)

def predict_gvi(lat, lon):
    return np.clip(0.2 + 0.15 * np.cos(lat), 0, 1)

def predict_bvi(lat, lon):
    return np.clip(0.5 - 0.1 * np.cos(lon), 0, 1)

def predict_pet(svf, gvi, bvi, temp, humidity, wind):
    # 예시용 PET 계산식 (실제 모델로 대체)
    return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + humidity * 0.03

# Streamlit UI
st.title("📍 위치 기반 PET 예측 시스템")
st.markdown("지도를 클릭하면 SVF, GVI, BVI를 기반으로 PET를 예측합니다.")

# 지도에서 위치 입력받기
location = st.text_input("위치를 입력하거나 클릭해보세요 (예: 부산대학교)", "부산대학교")
lat = st.number_input("위도", value=35.2325, format="%.6f")
lon = st.number_input("경도", value=129.0840, format="%.6f")

# 실시간 기상값 (예: OpenWeather API로 대체 가능)
temperature = 26.8  # ℃
humidity = 65       # %
wind_speed = 5.1    # m/s

if st.button("예측하기"):
    # 예측
    svf = predict_svf(lat, lon)
    gvi = predict_gvi(lat, lon)
    bvi = predict_bvi(lat, lon)
    predicted_pet = predict_pet(svf, gvi, bvi, temperature, humidity, wind_speed)

    # 결과 출력 (모바일 대응 최적화)
    st.markdown(f"""
    ### 📍 선택한 위치 정보
    - 위도: **{lat:.4f}**
    - 경도: **{lon:.4f}**

    ### 🌡 기상 정보
    - 기온: **{temperature} ℃**
    - 습도: **{humidity} %**
    - 풍속: **{wind_speed} m/s**

    ### 🌿 시각 환경 지표
    - SVF: **{svf:.3f}**
    - GVI: **{gvi:.3f}**
    - BVI: **{bvi:.3f}**

    ### 🔥 예측 PET 결과
    - 체감온도(PET): **{predicted_pet:.2f} ℃**
    """)

# 지도 시각화 (선택사항)
import pydeck as pdk

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=15,
        pitch=45,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=pd.DataFrame({'lat': [lat], 'lon': [lon]}),
            get_position='[lon, lat]',
            get_color='[255, 0, 0, 160]',
            get_radius=20,
        ),
    ],
))
