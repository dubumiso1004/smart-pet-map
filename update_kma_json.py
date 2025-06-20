import requests
import json
from datetime import datetime
import math

# 격자 변환 함수
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
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)
    ra = math.tan(math.pi * 0.25 + 35.233 * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = 129.08 * DEGRAD - olon
    if theta > math.pi: theta -= 2.0 * math.pi
    if theta < -math.pi: theta += 2.0 * math.pi
    theta *= sn
    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y

# 위경도 → 격자
x, y = convert_to_grid(35.233, 129.08)

# 기상청 API 호출
base_date = datetime.now().strftime("%Y%m%d")
base_time = "1100"  # 가장 가까운 발표 시각
api_key = "A31pZ0/UXicpgY0R38O7jPVsY6/dplQ/PTmiPKsh60m1UQ1hi57a++s7CkLJgOlCWgFxadK2vn33spFyP4/0gw=="  # 🔑 기상청 인증키

url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
params = {
    "serviceKey": api_key,
    "pageNo": "1",
    "numOfRows": "1000",
    "dataType": "JSON",
    "base_date": base_date,
    "base_time": base_time,
    "nx": x,
    "ny": y
}

response = requests.get(url, params=params, verify=False)
data = response.json()

# 필요한 값 추출
items = data["response"]["body"]["items"]["item"]
latest_time = max(item["fcstTime"] for item in items)
values = {item["category"]: item["fcstValue"] for item in items if item["fcstTime"] == latest_time}

# 저장할 데이터
result = {
    "airtemperature": float(values.get("T1H", -999)),
    "humidity": float(values.get("REH", -999)),
    "windspeed": float(values.get("WSD", -999))
}

# JSON 파일로 저장
with open("kma_latest_weather.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ 기상청 데이터 저장 완료:", result)
