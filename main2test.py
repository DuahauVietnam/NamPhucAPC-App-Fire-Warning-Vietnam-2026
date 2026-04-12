import os
import requests  # <-- ĐÂY LÀ DÒNG ĐANG THIẾU
import time
import pandas as pd
# -*- coding: utf-8 -*-
# Lấy mã từ biến môi trường của GitHub
NASA_MAP_KEY = os.getenv("NASA_MAP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Tọa độ Tây Nguyên (Bounding Box)
AREA = "107,11.5,110,15.5" 
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=payload)
    
    # Dòng này sẽ in ra kết quả phản hồi của Telegram lên GitHub Log
    print(f"Kết quả gửi Telegram: {response.status_code} - {response.text}")


def check_for_fires():
    # 1. Chế độ TEST nhanh: 
    # Đặt TEST_MODE = True nếu bạn muốn nhận tin nhắn báo cháy ngay lập tức
    TEST_MODE = True 

    if TEST_MODE:
        print("--- ĐANG CHẠY CHẾ ĐỘ TEST GIẢ LẬP ---")
        # Đây là dòng dữ liệu giả lập giống hệt định dạng của NASA
        data_to_process = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp,daynight\n14.352,108.123,340.5,0.4,0.4,2026-04-12,08:30,N,95,6.1N,285.4,15.2,D"
    else:
        # Chế độ chạy thật: Lấy dữ liệu từ NASA
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_MAP_KEY}/VIIRS_SNPP_NRT/{AREA}/1"
        response = requests.get(url)
        if response.status_code == 200:
            data_to_process = response.text
        else:
            print(f"Lỗi NASA: {response.status_code}")
            return

    # 2. Xử lý dữ liệu (Dùng chung cho cả thật và giả lập)
    lines = data_to_process.strip().split('\n')
    
    if len(lines) > 1:
        # Có dữ liệu (hoặc đang ở chế độ Test)
        latest_fire = lines[1].split(',')
        lat, lon = latest_fire[0], latest_fire[1]
        conf = latest_fire[8]
        
        alert_msg = (
            f"🔥 **TEST: CẢNH BÁO CHÁY GIẢ LẬP**\n\n"
            f"📍 Vị trí: `{lat}, {lon}`\n"
            f"💪 Độ tin cậy: {conf}%\n"
            f"⏰ Giờ kiểm tra: {time.strftime('%H:%M:%S')}\n\n"
            f"🔗 [Mở Google Maps](https://www.google.com/maps?q={lat},{lon})"
        )
        send_telegram_alert(alert_msg)
        print("Đã gửi tin nhắn Test thành công!")
    else:
        # Trường hợp thật mà không có cháy
        send_telegram_alert("🌿 Mọi thứ đều xanh tươi!")

        

# Chạy kiểm tra
check_for_fires()
