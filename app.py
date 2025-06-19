import streamlit as st
import pandas as pd
import joblib
import requests
from streamlit_folium import st_folium
import folium

# 설정
st.set_page_config(layout="wide")
st.title("🌡️ 스마트 PET 예측 지도")

# ----------------------- 모델 & 데이터 로드 -----------------------
model = joblib.load("pet_rf_model_full.pkl")

def dms_to_decimal(dms_str):
    try:
        parts = list(map(float, str(dms_str).split(";")))
        return parts[0] + parts[1]/60 + parts[2]/3600
    except:
        return None

# 엑셀 불러오기 및 좌표 변환
df = pd.read_excel("total_svf_gvi_bvi_250613.xlsx")
df = df.dropna(subset=["Lat", "Lon", "SVF", "GVI", "BVI"])
df["Lat_decimal"] = df["Lat"].apply(dms_to_decimal)
df["Lon_decimal"] = df["Lon"].apply(dms_to_decimal)

# ----------------------- 실시간 날씨 API -----------------------
API_KEY = "2ced117aca9b446ae43cf82401d542a8"

def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()
        air_temp = response.get("main", {}).get("temp", None)
        humidity = response.get("main", {}).get("humidity", None)
        wind_speed = response.get("wind", {}).get("speed", None)
        return air_temp, humidity, wind_speed
    except Exception as e:
        st.warning(f"API 요청 오류: {e}")
        return None, None, None

# ----------------------- PET 예측 함수 -----------------------
def predict_pet(svf, gvi, bvi, temp, humid, wind):
    X = pd.DataFrame([[svf, gvi, bvi, temp, humid, wind]], columns=["SVF", "GVI", "BVI", "AirTemperature", "Humidity", "WindSpeed"])
    return model.predict(X)[0]

# ----------------------- 가장 가까운 지점의 시각요소 추출 -----------------------
def get_nearest_visuals(lat, lon):
    df["distance"] = ((df["Lat_decimal"] - lat)**2 + (df["Lon_decimal"] - lon)**2)**0.5
    nearest = df.loc[df["distance"].idxmin()]
    return nearest["SVF"], nearest["GVI"], nearest["BVI"]

# ----------------------- 지도 출력 -----------------------
st.markdown("### 🗺️ 지도에서 위치를 클릭하세요")
start_coords = [35.1796, 129.0756]  # 부산 중심
m = folium.Map(location=start_coords, zoom_start=16)
m.add_child(folium.LatLngPopup())
map_result = st_folium(m, height=500, width=700)

# ----------------------- 클릭 이벤트 처리 -----------------------
if map_result and map_result.get("last_clicked"):
    lat = map_result["last_clicked"]["lat"]
    lon = map_result["last_clicked"]["lng"]
    st.success(f"📍 선택된 위치: {lat:.5f}, {lon:.5f}")

    svf, gvi, bvi = get_nearest_visuals(lat, lon)
    st.write(f"🪟 SVF: {svf:.3f} / 🌿 GVI: {gvi:.3f} / 🏢 BVI: {bvi:.3f}")

    air_temp, humidity, wind_speed = get_weather(lat, lon)

    if None not in (air_temp, humidity, wind_speed):
        st.write(f"🌤️ 기온: {air_temp}°C / 💧 습도: {humidity}% / 🍃 풍속: {wind_speed} m/s")
        pet = predict_pet(svf, gvi, bvi, air_temp, humidity, wind_speed)
        st.success(f"🔥 예측된 PET: {pet:.2f} °C")
    else:
        st.warning("⚠️ 실시간 기상 데이터를 불러올 수 없습니다.")