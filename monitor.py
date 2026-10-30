import os
import requests

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "vzduch-bratislava-slovnaft-alert")

LIMITS = {
    "pm25": 30.0,
    "pm10": 45.0,
    "so2": 100.0,
}

STATIONS_OF_INTEREST = [
    "Podunajské Biskupice",
    "Rovinka",
    "Trnavské mýto",
    "Kamenné námestie",
    "Mamateyova"
]

def send_notification(station_name: str, issue_text: str):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    title = f"Zatvoriť okná! Zhoršený vzduch: {station_name}"
    message = (
        f"Pozor na vetranie. Boli namerané zvýšené hodnoty:\n"
        f"{issue_text}\n"
        f"Zdroj: monitorovacia sieť ovzdušia"
    )
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": "high",
        "Tags": "no_entry_sign,factory,wind_blowing_face"
    }
    resp = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=10)
    resp.raise_for_status()
    print(f"Upozornenie odoslané pre: {station_name}")

def check_air_quality():
    api_url = "https://dnes.dycham.sk/api/stations"
    headers = {"User-Agent": "BratislavaAirQualityNotifier/1.0"}

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        stations = response.json()
    except Exception as e:
        print(f"Chyba pri sťahovaní dát: {e}")
        return

    for station in stations:
        name = station.get("name", "")
        if any(target.lower() in name.lower() for target in STATIONS_OF_INTEREST):
            pm25 = float(station.get("pm25") or 0)
            pm10 = float(station.get("pm10") or 0)
            so2 = float(station.get("so2") or 0)
            air_index = station.get("aqi_label", "")

            exceeded = []
            if pm25 >= LIMITS["pm25"]:
                exceeded.append(f"PM2.5: {pm25} µg/m³ (limit {LIMITS['pm25']})")
            if pm10 >= LIMITS["pm10"]:
                exceeded.append(f"PM10: {pm10} µg/m³ (limit {LIMITS['pm10']})")
            if so2 >= LIMITS["so2"]:
                exceeded.append(f"SO2: {so2} µg/m³ (limit {LIMITS['so2']})")

            if exceeded or air_index in ["Zhoršená", "Zlá", "Veľmi zlá"]:
                details = "\n".join(exceeded) if exceeded else f"Index: {air_index}"
                send_notification(name, details)
            else:
                print(f"Stanica {name}: v norme (PM2.5: {pm25}, PM10: {pm10}, SO2: {so2}).")

if __name__ == "__main__":
    check_air_quality()
