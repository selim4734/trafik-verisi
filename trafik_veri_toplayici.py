"""
İstanbul Trafik Veri Toplayıcı - TEK SEFERLİK ÇALIŞTIRMA
===========================================================
Bu script TEK BİR ölçüm alır ve CSV dosyasına ekler (append).
15 dakikada bir otomatik çalışması için işletim sisteminin
zamanlayıcısına (cron / Task Scheduler) eklenmesi gerekir.
Aşağıda kurulum talimatları var.

Veri kaynağı: TomTom Traffic Flow API (ücretsiz katman: günde 2.500 istek)
Neden TomTom: Google Maps API kredi kartı istiyor, TomTom ücretsiz
başlangıç için kredi kartsız API key veriyor.

Kurulum:
    1) https://developer.tomtom.com adresinden ücretsiz hesap aç
    2) "Traffic API" için bir API key oluştur
    3) Aşağıdaki API_KEY değişkenine yapıştır
    4) pip install requests
"""

import csv
import os
import requests
from datetime import datetime, timezone

API_KEY = "UlJdBNmmjKRiuIYap9cn3duVVQrjYeqB"

OUTPUT_FILE = "istanbul_trafik_verisi.csv"

# Her ilçe için 2 temsili nokta (ana cadde/kavşak). İstersen daha fazla
# nokta ekleyebilirsin (daha hassas ama daha çok API isteği demek).
DISTRICT_POINTS = {
    "Fatih":         [(41.0128, 28.9528), (41.0179, 28.9391)],   # Aksaray, Vatan Cd.
    "Sisli":         [(41.0553, 28.9880), (41.0672, 28.9950)],   # Osmanbey, Mecidiyeköy
    "Zeytinburnu":   [(40.9950, 28.9020), (41.0000, 28.9100),    # Sahil yolu, Merkezefendi
                       (40.9880, 28.9050),                        # Maltepe Mahallesi
                       (40.9950, 28.9050),                        # 10. Yıl Caddesi
                       (40.9850, 28.8950)],                       # Kennedy Caddesi (sahil)
    "Gungoren":      [(41.0200, 28.8757), (41.0158, 28.8683)],   # Güngören Merkez, Haznedar
    "Bakirkoy":      [(40.9819, 28.8772), (40.9880, 28.8700),    # Bakırköy Meydan, İncirli
                       (40.9750, 28.8480),                        # Ataköy
                       (40.9750, 28.7850)],                       # Florya
    "Kucukcekmece":  [(41.0140, 28.7860), (40.9900, 28.7800)],   # Halkalı, Sefaköy
    "Bagcilar":      [(41.0380, 28.8570), (41.0450, 28.8450)],   # Bağcılar Meydan, Yenimahalle
    "Basaksehir":    [(41.0950, 28.8010), (41.1150, 28.8000)],   # Başakşehir Merkez, Kayaşehir
    "Besiktas":      [(41.0430, 29.0080), (41.0820, 29.0100)],   # Beşiktaş Meydan, Levent
}

TOMTOM_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


def get_flow(lat, lon):
    params = {"point": f"{lat},{lon}", "key": API_KEY}
    resp = requests.get(TOMTOM_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()["flowSegmentData"]
    current = data["currentSpeed"]
    free_flow = data["freeFlowSpeed"]
    congestion = 1 - (current / free_flow) if free_flow else None
    return current, free_flow, congestion


def main():
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    rows = []
    for district, points in DISTRICT_POINTS.items():
        for lat, lon in points:
            try:
                current, free_flow, congestion = get_flow(lat, lon)
                rows.append({
                    "timestamp": timestamp,
                    "district": district,
                    "lat": lat,
                    "lon": lon,
                    "current_speed": current,
                    "free_flow_speed": free_flow,
                    "congestion_ratio": round(congestion, 3) if congestion is not None else "",
                })
                print(f"{district} ({lat},{lon}): {current}/{free_flow} km/h -> yoğunluk {congestion:.2f}")
            except Exception as e:
                print(f"HATA - {district} ({lat},{lon}): {e}")

    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "district", "lat", "lon",
            "current_speed", "free_flow_speed", "congestion_ratio"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} satır '{OUTPUT_FILE}' dosyasına eklendi.")


if __name__ == "__main__":
    main()
