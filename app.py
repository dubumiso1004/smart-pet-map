import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import requests

# ---------------------------
# 1. 실측 데이터 불러오기
# ---------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("total_svf_gvi_bvi_250613.xlsx")
    
    def dms_to_decimal(dms_str):
        try:
            d, m, s = [float(x) for x in dms_str.split(";")]
            return d + m/60 + s/3600
        except:
            return None
    
    df["Lat_decimal"] = df["Lat"].apply(dms_to_decimal)
    df["Lon_decimal"] = df["Lon"].apply(dms_to_decimal)
    return df

df = load_data()

# ---------------------------
# 2. 가장 가까운 지점 찾기
# ---------------------------
def find_nearest_point(lat_clicked, lon_clicked, df):
    df["distance"] = df.apply(
        lambda row: geodesic((lat_clicked, lon_clicked), (row["Lat_decimal"], row["Lon_decimal"])).meters,
        axis=1
    )
    return df.sort_values("distance").iloc[0]

# ---------------------------
# 3. 실시간 날씨 불러오기
# ---------------------------
def get_weather(lat, lon, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        return temp, humidity, wind_speed
    except:
        return None, None, None

# ---------------------------
# 4. PET 예측 수식 (기초 회귀모델)
# ---------------------------
def predict_pet(svf, gvi, bvi, temp, hum, wind):
    return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

# ---------------------------
# 5. Streamlit 앱 실행
# ---------------------------
st.set_page_config(layout="centered")
st.title("📍 지도 기반 실측 + 실시간 PET 예측 시스템")
st.markdown("지도를 클릭하면 가장 가까운 측정지점의 실측값과 실시간 날씨를 기반으로 PET를 예측합니다.")

# 지도 생성
center = [35.2325, 129.0840]
m = folium.Map(location=center, zoom_start=17)
map_data = st_folium(m, height=500)

# 클릭 이벤트 처리
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    nearest = find_nearest_point(lat, lon, df)

    # 실시간 날씨 불러오기
    api_key = "2ced117aca9b446ae43cf82401d542a8"
    temp_now, hum_now, wind_now = get_weather(lat, lon, api_key)

    # 📍 위치 표시
    st.success(f"✅ 클릭된 위치: 위도 {lat:.5f}, 경도 {lon:.5f}")

    # 실측 데이터 출력
    st.markdown("### 📍 가장 가까운 측정지점 (실측 데이터)")
    st.markdown(f"""
    - **ID**: `{nearest['ID']}`  
    - **지점명**: `{nearest['Location_Name']}`  
    - **거리**: `{nearest['distance']:.1f} m`  
    - **SVF**: `{nearest['SVF']:.3f}`  
    - **GVI**: `{nearest['GVI']:.3f}`  
    - **BVI**: `{nearest['BVI']:.3f}`  
    - **기온**: `{nearest['AirTemperature']:.1f} ℃`  
    - **습도**: `{nearest['Humidity']:.1f} %`  
    - **풍속**: `{nearest['WindSpeed']:.1f} m/s`  
    - **실측 PET**: `{nearest['PET']:.2f} ℃`
    """)

    # 실시간 날씨 출력
    st.markdown("### 🌐 실시간 기상 정보 (OpenWeatherMap)")
    if temp_now is not None:
        st.markdown(f"""
        - **기온**: `{temp_now:.1f} ℃`  
        - **습도**: `{hum_now:.1f} %`  
        - **풍속**: `{wind_now:.1f} m/s`
        """)
        
        # 실시간 PET 예측
        pet_estimated = predict_pet(
            nearest['SVF'], nearest['GVI'], nearest['BVI'],
            temp_now, hum_now, wind_now
        )
        st.markdown("### 🔥 예측 PET (실시간 기상 기반)")
        st.markdown(f"- PET 예측값: `{pet_estimated:.2f} ℃`")
    else:
        st.warning("⚠️ 실시간 기상 데이터를 가져오지 못했습니다.")
else:
    st.info("🖱 지도에서 예측할 위치를 클릭하세요.")
