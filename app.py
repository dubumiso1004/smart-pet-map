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
# 3. 실시간 날씨 API 호출
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
# 4. Streamlit 앱 시작
# ---------------------------
st.set_page_config(layout="centered")
st.title("📍 지도 기반 실측+실시간 PET 예측 시스템")
st.markdown("지도에서 위치를 클릭하면 가장 가까운 측정지점의 실측값과 실시간 기상 정보를 함께 확인합니다.")

# ---------------------------
# 5. 지도 출력 및 클릭 처리
# ---------------------------
center = [35.2325, 129.0840]
m = folium.Map(location=center, zoom_start=17)
map_data = st_folium(m, height=500)

# 🔍 디버깅용 클릭 확인
st.write("🧪 클릭 데이터 확인:", map_data)

# ---------------------------
# 6. 클릭 처리 및 결과 출력
# ---------------------------
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    # 가장 가까운 측정지점 찾기
    nearest = find_nearest_point(lat, lon, df)

    # 실시간 날씨 정보
    api_key = "2ced117aca9b446ae43cf82401d542a8"
    temp_now, hum_now, wind_now = get_weather(lat, lon, api_key)

    # 📍 선택 위치 결과 출력
    st.success(f"✅ 클릭된 위치: 위도 {lat:.5f}, 경도 {lon:.5f}")
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

    st.markdown("### 🌐 실시간 기상 정보 (OpenWeatherMap)")
    if temp_now is not None:
        st.markdown(f"""
        - **기온**: `{temp_now:.1f} ℃`  
        - **습도**: `{hum_now:.1f} %`  
        - **풍속**: `{wind_now:.1f} m/s`
        """)
    else:
        st.warning("⚠️ 실시간 기상 데이터를 불러오지 못했습니다.")
else:
    st.info("🖱 지도에서 예측할 위치를 클릭하세요.")
