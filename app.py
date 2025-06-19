import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import requests
import datetime
import math

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
# 3. 기상청 API 기반 실시간 날씨
# ---------------------------
def get_weather_kma(nx, ny):
    try:
        service_key = "A31pZ0%2FUXicpgY0R38O7jPVsY6%2FdplQ%2FPTmiPKsh60m1UQ1hi57a%2B%2Bs7CkLJgOlCWgFxadK2vn33spFyP4%2F0gw%3D%3D"
        now = datetime.datetime.now()
        base_date = now.strftime("%Y%m%d")
        hour = now.hour
        if now.minute < 45:
            hour -= 1
        base_time = f"{hour:02}00"

        url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst?serviceKey={service_key}&numOfRows=100&pageNo=1&dataType=JSON&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"
        res = requests.get(url)
        data = res.json()

        items = data['response']['body']['items']['item']
        temp = hum = wind = None
        for item in items:
            if item['category'] == 'T1H':
                temp = float(item['obsrValue'])
            elif item['category'] == 'REH':
                hum = float(item['obsrValue'])
            elif item['category'] == 'WSD':
                wind = float(item['obsrValue'])

        return temp, hum, wind
    except:
        return None, None, None

# ---------------------------
# 4. 위경도 → 기상청 격자 변환 함수
# ---------------------------
def convert_to_grid(lat, lon):
    RE = 6371.00877
    GRID = 5.0
    SLAT1 = 30.0
    SLAT2 = 60.0
    OLON = 126.0
    OLAT = 38.0
    XO = 43
    YO = 136

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn * math.cos(slat1)) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = ra * math.sin(theta) + XO + 0.5
    y = ro - ra * math.cos(theta) + YO + 0.5
    return int(x), int(y)

# ---------------------------
# 5. PET 예측 수식
# ---------------------------
def predict_pet(svf, gvi, bvi, temp, hum, wind):
    return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

# ---------------------------
# 6. Streamlit 앱 실행
# ---------------------------
st.set_page_config(layout="centered")
st.title("📍 지도 기반 실측 + 기상청 실시간 PET 예측 시스템")
st.markdown("지도를 클릭하면 가장 가까운 측정지점의 실측값과 **기상청 실시간 날씨**를 기반으로 PET를 예측합니다.")

# 지도 생성 및 클릭 이벤트 설정
center = [35.2325, 129.0840]
m = folium.Map(location=center, zoom_start=17)
m.add_child(folium.LatLngPopup())
folium.ClickForMarker(popup="선택 위치").add_to(m)  # ✅ 클릭 마커 추가

map_data = st_folium(m, height=500, returned_objects=["last_clicked"], use_container_width=True)

# 디버깅용 출력 (필요 시 주석 해제)
# st.write(map_data)

if map_data and map_data.get("last_clicked") is not None:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    nearest = find_nearest_point(lat, lon, df)
    nx, ny = convert_to_grid(lat, lon)
    temp_now, hum_now, wind_now = get_weather_kma(nx, ny)

    st.markdown("### 📌 선택된 위치")
    st.markdown(f"위도: `{lat:.5f}`, 경도: `{lon:.5f}`")

    st.markdown("### 📍 가장 가까운 측정지점 (실측 데이터)")
    st.markdown(f"""
    - **ID**: `{nearest['ID']}`  
    - **지점명**: `{nearest['Location_Name']}`  
    - **거리**: `{nearest['distance']:.1f} m`  
    - **SVF**: `{nearest['SVF']:.3f}`  
    - **GVI**: `{nearest['GVI']:.3f}`  
    - **BVI**: `{nearest['BVI']:.3f}`  
    - **실측 기온**: `{nearest['AirTemperature']:.1f} ℃`  
    - **실측 습도**: `{nearest['Humidity']:.1f} %`  
    - **실측 풍속**: `{nearest['WindSpeed']:.1f} m/s`  
    - **실측 PET**: `{nearest['PET']:.2f} ℃`
    """)

    if temp_now is not None:
        st.markdown("### 🌐 실시간 기상청 데이터")
        st.markdown(f"""
        - **기온**: `{temp_now:.1f} ℃`  
        - **습도**: `{hum_now:.1f} %`  
        - **풍속**: `{wind_now:.1f} m/s`
        """)
        pet_estimated = predict_pet(
            nearest['SVF'], nearest['GVI'], nearest['BVI'],
            temp_now, hum_now, wind_now
        )
        st.markdown("### 🔥 예측 PET (기상청 기반)")
        st.markdown(f"- 예측 PET: `{pet_estimated:.2f} ℃`")
    else:
        st.warning("⚠️ 기상청 실시간 데이터를 불러오지 못했습니다.")
else:
    st.info("🖱 지도에서 예측할 위치를 클릭하세요.")
