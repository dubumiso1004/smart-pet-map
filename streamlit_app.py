import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt

# ------------------------------
# 1. 모델 및 데이터 불러오기
# ------------------------------
@st.cache_data
def load_model():
    return joblib.load("pet_rf_model_trained.pkl")

@st.cache_data
def load_data():
    df = pd.read_excel("total_svf_gvi_bvi_250613.xlsx")
    return df

model = load_model()
df = load_data()

# ------------------------------
# 2. Streamlit UI 구성
# ------------------------------
st.title("🌡️ AI 기반 PET 예측 시스템")
st.markdown("위도, 경도 기반으로 SVF, GVI, BVI 및 기상데이터를 활용한 PET 예측")

selected_row = st.selectbox("📍 예측할 측정 지점 선택", df.index)

input_data = df.loc[selected_row, ['SVF', 'GVI', 'BVI', 'AirTemperature', 'Humidity', 'WindSpeed']]
input_df = pd.DataFrame([input_data])

# ------------------------------
# 3. PET 예측
# ------------------------------
predicted_pet = model.predict(input_df)[0]
st.success(f"✅ 예측 PET: **{predicted_pet:.2f}°C**")

# ------------------------------
# 4. SHAP 값 시각화
# ------------------------------
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(input_df)

st.subheader("📊 SHAP 기여도 (변수 중요도)")
fig, ax = plt.subplots()
shap.plots._waterfall.waterfall_legacy(explainer.expected_value, shap_values[0], input_df.iloc[0], max_display=6, show=False)
st.pyplot(fig)

# ------------------------------
# 5. 원본 입력값 표출
# ------------------------------
st.subheader("📄 입력값 확인")
st.dataframe(input_df.style.format(precision=2))
