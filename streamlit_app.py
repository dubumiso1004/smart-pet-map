import streamlit as st
import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt

# 모델 로딩
@st.cache_resource
def load_model():
    return joblib.load("pet_rf_model_full.pkl")  # ← 파일명 수정됨

model = load_model()

# 페이지 제목
st.markdown("🎯 **AI 기반 PET 예측 시스템**")
st.markdown("위도, 경도 기반으로 SVF, GVI, BVI 및 기상데이터를 활용한 PET 예측")

# 사용자 입력
svf = st.slider("SVF (Sky View Factor)", 0.0, 1.0, 0.5, 0.01)
gvi = st.slider("GVI (Green View Index)", 0.0, 1.0, 0.3, 0.01)
bvi = st.slider("BVI (Building View Index)", 0.0, 1.0, 0.3, 0.01)
temp = st.slider("기온 (°C)", 10.0, 40.0, 25.0, 0.5)
humidity = st.slider("습도 (%)", 10.0, 100.0, 60.0, 1.0)
wind = st.slider("풍속 (m/s)", 0.0, 10.0, 1.0, 0.1)

# 입력 데이터프레임 구성
input_df = pd.DataFrame({
    "SVF": [svf],
    "GVI": [gvi],
    "BVI": [bvi],
    "AirTemperature": [temp],
    "Humidity": [humidity],
    "WindSpeed": [wind],
})

# PET 예측
prediction = model.predict(input_df)[0]
st.success(f"예측된 PET: **{prediction:.2f} °C**")

# SHAP 해석 (CPU 기반)
st.markdown("📊 **변수 영향력 분석 (SHAP)**")
explainer = shap.Explainer(model.predict, input_df, algorithm="permutation")
shap_values = explainer(input_df)

fig, ax = plt.subplots()
shap.summary_plot(shap_values, input_df, show=False)
st.pyplot(fig)

