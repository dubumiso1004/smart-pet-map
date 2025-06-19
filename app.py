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
            return d + m / 60 + s / 3600
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
# 4. 격자 변환 함수 (위경도 → nx, ny)
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
# 5. PET 예측 수식 (기초 회귀모델)
# ---------------------------
def predict_pet(svf, gvi, bvi, temp, hum, wind):
    return temp + (1 - svf) * 5 - gvi * 2 + bvi * 1.5 - wind * 0.5 + hum * 0.03

# ---------------------------
# 6. Streamlit 앱 실행
# ---------------------------
st.set_page_config(layout="centered")
st.title("📍 PET 예측 시스템")
st.markdown("지도를 클릭하면 가장 가까운 측정지점의 실측값과 **기상청 실시간 날씨**를 기반으로 PET를 예측합니다.")

# 지도 생성
center = [35.2325, 129.0840]
m = folium.Map(location=center, zoom_start=17)
folium.ClickForMarker(popup="선택 위치").add_to(m)
map_data = st_folium(m, height=500, returned_objects=["last_clicked"], use_container_width=True)

# 클릭 이벤트 처리
if map_data and "last_clicked" in map_data and map_data["last_clicked"] is not None:
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]

    # 가장 가까운 지점 탐색
    nearest = find_nearest_point(clicked_lat, clicked_lon, df)

    # 격자 변환 및 기상 데이터 가져오기
    nx, ny = convert_to_grid(clicked_lat, clicked_lon)
    temp, hum, wind = get_weather_kma(nx, ny)

    if None not in [temp, hum, wind]:
        pet = predict_pet(nearest["SVF"], nearest["GVI"], nearest["BVI"], temp, hum, wind)

        # 결과 출력
        st.subheader("📌 예측 결과")
        st.write(f"**선택 위치:** {clicked_lat:.5f}, {clicked_lon:.5f}")
        st.write(f"**가장 가까운 지점:** {nearest['Location_Name']} (거리: {nearest['distance']:.1f} m)")
        st.write(f"**실시간 기온:** {temp:.1f}°C, **습도:** {hum:.0f}%, **풍속:** {wind:.1f} m/s")
        st.markdown(f"### 🧠 예측 PET: `{pet:.1f}°C`")
    else:
        st.warning("⚠️ 실시간 기상 데이터를 불러올 수 없습니다.")
