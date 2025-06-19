import streamlit as st
import pandas as pd
import numpy as np
import joblib
from geopy.distance import geodesic

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

# ---------------------------
# 2. 가장 가까운 측정지점 찾기
# ---------------------------
def find_nearest_point(lat, lon, df):
    clicked_point = (lat, lon)
    df["Distance"] = df.apply(lambda row: geodesic(clicked_point, (row["Lat_decimal"], row["Lon_decimal"])).meters, axis=1)
    return df.loc[df["Distance"].idxmin()]

# ---------------------------
# 3. 모델 불러오기
# ---------------------------
@st.cache_resource
def load_model():
    return joblib.load("pet_predict_rf_model.pkl")

# ---------------------------
# 4. Streamlit 메인 함수
# ---------------------------
def main():
    st.title("🌡️ AI 기반 PET 예측 시스템")
    st.markdown("위도, 경도 기반으로 SVF, GVI, BVI 및 기상데이터를 활용한 PET 예측")

    df = load_data()
    model = load_model()

    lat = st.number_input("위도 입력 (예: 35.232)", value=35.232, format="%.6f")
    lon = st.number_input("경도 입력 (예: 129.084)", value=129.084, format="%.6f")

    if st.button("PET 예측하기"):
        nearest = find_nearest_point(lat, lon, df)

        svf = nearest["SVF"]
        gvi = nearest["GVI"]
        bvi = nearest["BVI"]
        temp = nearest["AirTemperature"]
        hum = nearest["Humidity"]
        wind = nearest["WindSpeed"]

        input_data = pd.DataFrame([{
            "SVF": svf,
            "GVI": gvi,
            "BVI": bvi,
            "AirTemperature": temp,
            "Humidity": hum,
            "WindSpeed": wind
        }])

        predicted_pet = model.predict(input_data)[0]

        st.subheader("📍 예측 결과")
        st.markdown(f"**SVF:** {svf:.3f}, **GVI:** {gvi:.3f}, **BVI:** {bvi:.3f}")
        st.markdown(f"**기온:** {temp:.1f}℃, **습도:** {hum:.1f}%, **풍속:** {wind:.1f} m/s")
        st.success(f"👉 예측 PET: **{predicted_pet:.2f}℃**")

if __name__ == "__main__":
    main()
