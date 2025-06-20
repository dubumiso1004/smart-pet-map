from flask import Flask, request, jsonify
import requests
from datetime import datetime
import math

app = Flask(__name__)

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
    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi: theta -= 2.0 * math.pi
    if theta < -math.pi: theta += 2.0 * math.pi
    theta *= sn
    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y

@app.route("/kma", methods=["GET"])
def get_kma():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    x, y = convert_to_grid(lat, lon)

    base_date = datetime.now().strftime('%Y%m%d')
    base_time = "1100"
    service_key = "A31pZ0/UXicpgY0R38O7jPVsY6/dplQ/PTmiPKsh60m1UQ1hi57a++s7CkLJgOlCWgFxadK2vn33spFyP4/0gw=="  # 🔑 여기에 실제 API 키 입력

    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": x,
        "ny": y
    }

    response = requests.get(url, params=params, verify=False)
    items = response.json()["response"]["body"]["items"]["item"]
    latest_time = max(item["fcstTime"] for item in items)
    values = {item["category"]: item["fcstValue"] for item in items if item["fcstTime"] == latest_time}

    return jsonify({
        "airtemperature": float(values.get("T1H", -999)),
        "humidity": float(values.get("REH", -999)),
        "windspeed": float(values.get("WSD", -999))
    })

if __name__ == "__main__":
    app.run(port=5000)
