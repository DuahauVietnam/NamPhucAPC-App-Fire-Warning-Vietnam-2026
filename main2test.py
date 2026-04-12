import os
import requests  # <-- ĐÂY LÀ DÒNG ĐANG THIẾU
import time
import pandas as pd
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
# Tính toán giờ Việt Nam (UTC+7)
now_utc = datetime.utcnow()
now_vn = now_utc + timedelta(hours=7)
gio_hien_tai = now_vn.strftime('%H:%M:%S %D')

# Lấy mã từ biến môi trường của GitHub
NASA_MAP_KEY = os.getenv("NASA_MAP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OW_KEY = os.getenv("OW_KEY")

### LẤY ĐỊA CHỈ TỪ TỌA ĐỘ
def get_location_name(lat, lon):
    try:
        # Thêm tham số limit=1 và appid
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OW_KEY}"
        response = requests.get(url)
        res = response.json()
        
        if response.status_code == 200 and len(res) > 0:
            location = res[0]
            
            # Ưu tiên lấy tên tiếng Việt trong mục local_names
            names = location.get('local_names', {})
            name_vi = names.get('vi') 
            
            # Nếu không có tên tiếng Việt riêng, lấy tên mặc định
            display_name = name_vi if name_vi else location.get('name', '')
            state = location.get('state', '')
            
            # Dịch một số tên tỉnh phổ biến nếu OpenWeather trả về tiếng Anh
            tinh_thanh = {
                "Gia Lai Province": "Tỉnh Gia Lai",
                "Kon Tum Province": "Tỉnh Kon Tum",
                "Dak Lak Province": "Tỉnh Đắk Lắk",
                "Dak Nong Province": "Tỉnh Đắk Nông",
                "Lam Dong Province": "Tỉnh Lâm Đồng"
            }
            state_vi = tinh_thanh.get(state, state)
            
            return f"{display_name}, {state_vi}"
        return "Khu vực rừng núi (Chưa xác định)"
    except Exception as e:
        print(f"Lỗi lấy địa danh: {e}")
        return "Tọa độ tại Tây Nguyên"

def get_fire_danger(temp, humidity):
    if temp > 35 and humidity < 30:
        return "🔴 CẤP V (CỰC KỲ NGUY HIỂM)"
    elif temp > 32 and humidity < 40:
        return "🟠 CẤP IV (NGUY HIỂM)"
    elif temp > 28 and humidity < 50:
        return "🟡 CẤP III (CAO)"
    else:
        return "🟢 CẤP I - II (THẤP/TRUNG BÌNH)"


def get_weather(lat, lon):
    try:
        # Sử dụng API Current Weather Data
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OW_KEY}&units=metric"
        res = requests.get(url).json()
        temp = res['main']['temp']
        humidity = res['main']['humidity']
        wind_speed = res['wind']['speed'] # Tốc độ gió (m/s)
        # Chuyển m/s sang km/h cho phổ thông
        wind_kmh = round(wind_speed * 3.6, 1)
        return temp, humidity, wind_kmh
    except:
        return None, None, None
        
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

        # 1. Lấy địa danh
        dia_danh = get_location_name(lat, lon)
        # 2. Lấy thời tiết (nhiệt độ, độ ẩm, hướng gió)
        temp, humidity, wind_kmh = get_weather(lat, lon)  
        cap_bao_dong = get_fire_danger(temp, humidity)
        weather_info = f"🌡 Nhiệt độ: {temp}°C | 💧 Độ ẩm: {humidity}%" if temp else "⚠️ Không lấy được dữ liệu thời tiết"
         # Giờ Việt Nam
        now_vn = datetime.utcnow() + timedelta(hours=7)
        gio_vn = now_vn.strftime('%H:%M:%S %D')

        
        alert_msg = (
            f"🔥 🔥 🔥 \n"
            f"⚠️ **TEST: CẢNH BÁO NGUY CƠ CHÁY KHẨN CẤP **\n"
            f"----------------------------------\n"
            f"📍 **Địa danh:** {dia_danh}\n"
            f"🌍 **Tọa độ:** `{lat}, {lon}`\n"
            f"🔗 [Mở Bản Đồ Vệ Tinh](https://www.google.com/maps?q={lat},{lon}&t=k)\n\n"
            f"🌡  {temp}°C 🌡\n"
            f"💧 {humidity}% 💧\n"
            f"💨 {wind_kmh} kmh 💨\n"
            f"⚠️ **Dự báo :** {cap_bao_dong}\n"
            f"----------------------------------\n"
            f"⏰ **Cập nhật:** {gio_vn} (Giờ VN)\n"
            f"💪 Độ tin cậy: {conf}%\n\n"
            f" Lưu ý: Nếu Cảnh báo có cháy, nhưng độ ẩm khu vực đó đang là 90% và đang có mưa, bạn có thể nghi ngờ đó là lỗi cảm biến hoặc cháy nhỏ đã bị dập tắt.\n"
            f" Đánh giá mức độ nguy hiểm: Nếu nhiệt độ là > 39°C và độ ẩm < 25%, đó là tình trạng cực kỳ khẩn cấp, cần báo động ngay lập tức."
            f" (Copyright 2026 - NamPhucAPC - 0888801202) "
            f" 🇻🇳  🆘 Hotline báo cháy ☎️ 1️⃣1️⃣4️⃣"
                       
        )
        send_telegram_alert(alert_msg)
        print("Đã gửi tin nhắn Test thành công!")
    else:
        # Trường hợp thật mà không có cháy
        send_telegram_alert("🌿 Mọi thứ đều xanh tươi!")

        

# Chạy kiểm tra
check_for_fires()
