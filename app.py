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
        lambda row: geodesic((lat_clicked, lon_clicked), (row["Lat_decimal"], row["Lon_decimal"]))
        .meters,
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