import streamlit as st
import pandas as pd
import joblib
import requests
from math import radians, cos, sin, sqrt, atan2
import folium
from streamlit_folium import st_folium

# ----------------------- 설정 -----------------------
st.set_page_config(layout="wide")
st.title("🌡️ 스마트 PET 예측 지도 시스템")

# ----------------------- 모델 & 데이터 로드 -----------------------
model = joblib.load("pet_rf_model_full.pkl")
df = pd.read_excel("total_svf_gvi_bvi_250613.xlsx")

# ----------------------- 실시간 날씨 API -----------------------
API_KEY = "2ced117aca9b446ae43cf82401d542a8"

def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()
        air_temp = response["main"]["temp"]
        humidity = response["main"]["humidity"]
        wind_speed = response["wind"]["speed"]
        return air_temp, humidity, wind_speed
    except:
        return None, None, None

# ----------------------- 가장 가까운 지점의 SVF/GVI/BVI 추출 -----------------------
def get_nearest_visuals(lat, lon):
    df["distance"] = ((df["Lat_decimal"] - lat)**2 + (df["Lon_decimal"] - lon)**2)**0.5
    nearest = df.loc[df["distance"].idxmin()]
    return nearest["SVF"], nearest["GVI"], nearest["BVI"]

# ----------------------- PET 예측 함수 -----------------------
def predict_pet(svf, gvi, bvi, temp, humid, wind):
    X = pd.DataFrame([[svf, gvi, bvi, temp, humid, wind]], columns=["SVF", "GVI", "BVI", "AirTemperature", "Humidity", "WindSpeed"])
    return model.predict(X)[0]

# ----------------------- 지도 출력 -----------------------
start_coords = (35.133, 129.045)  # 부산대 중심
m = folium.Map(location=start_coords, zoom_start=16)

# 클릭 이벤트 수신
click_data = st_folium(m, width=700, height=500)

if click_data and click_data["last_clicked"]:
    clicked_lat = click_data["last_clicked"]["lat"]
    clicked_lon = click_data["last_clicked"]["lng"]
    st.success(f"📍 선택된 위치: {clicked_lat:.5f}, {clicked_lon:.5f}")

    # 시각요소 추정
    svf, gvi, bvi = get_nearest_visuals(clicked_lat, clicked_lon)
    st.write(f"🪟 SVF: {svf:.3f} / 🌿 GVI: {gvi:.3f} / 🏢 BVI: {bvi:.3f}")

    # 실시간 날씨
    air_temp, humidity, wind_speed = get_weather(clicked_lat, clicked_lon)

    if air_temp is not None:
        st.write(f"🌤️ 기온: {air_temp}°C / 💧 습도: {humidity}% / 🍃 풍속: {wind_speed} m/s")
        pet = predict_pet(svf, gvi, bvi, air_temp, humidity, wind_speed)
        st.success(f"🔥 예측된 PET: {pet:.2f} °C")
    else:
        st.warning("⚠️ 실시간 기상 데이터를 불러올 수 없습니다.")
