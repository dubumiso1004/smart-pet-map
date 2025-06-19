import streamlit as st
import pandas as pd
import joblib
import requests
from streamlit_folium import st_folium
import folium

# 설정
st.set_page_config(layout="wide")
st.title("🌡️ 스마트 PET 예측 지도")

# 모델 및 데이터
model = joblib.load("pet_rf_model_full.pkl")
df = pd.read_excel("total_svf_gvi_bvi_250613.xlsx")
API_KEY = "2ced117aca9b446ae43cf82401d542a8"

# 지도 시작 위치 (원하는 위치로 변경 가능)
start_coords = [35.1796, 129.0756]  # 예: 부산 시청

# Folium 지도 생성
m = folium.Map(location=start_coords, zoom_start=15)

# 지도 클릭 처리
st.markdown("### 🗺️ 지도에서 위치를 클릭하세요")
map_result = st_folium(m, height=500, width=700)

if map_result and map_result.get("last_clicked"):
    lat = map_result["last_clicked"]["lat"]
    lon = map_result["last_clicked"]["lng"]
    st.success(f"📍 선택된 위치: {lat:.5f}, {lon:.5f}")

    # 가장 가까운 지점에서 시각요소 추출
    df["distance"] = ((df["Lat_decimal"] - lat)**2 + (df["Lon_decimal"] - lon)**2)**0.5
    nearest = df.loc[df["distance"].idxmin()]
    svf, gvi, bvi = nearest["SVF"], nearest["GVI"], nearest["BVI"]

    st.write(f"🪟 SVF: {svf:.3f} / 🌿 GVI: {gvi:.3f} / 🏢 BVI: {bvi:.3f}")

    # 날씨 API 호출
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        weather = requests.get(url).json()
        temp = weather["main"]["temp"]
        humidity = weather["main"]["humidity"]
        wind = weather["wind"]["speed"]

        st.write(f"🌤️ 기온: {temp}°C / 💧 습도: {humidity}% / 🍃 풍속: {wind} m/s")

        # PET 예측
        X = pd.DataFrame([[svf, gvi, bvi, temp, humidity, wind]],
                         columns=["SVF", "GVI", "BVI", "AirTemperature", "Humidity", "WindSpeed"])
        pet = model.predict(X)[0]
        st.success(f"🔥 예측된 PET: {pet:.2f} °C")
    except Exception as e:
        st.warning(f"기상 데이터 오류: {e}")
