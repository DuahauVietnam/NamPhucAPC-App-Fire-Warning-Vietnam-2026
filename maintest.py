import json
import os
import requests
import time
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -*- coding: utf-8 -*-

##================================================================ AREA
AREA = "107,11.5,110,15.5" 

##================================================================ API KEYS
NASA_MAP_KEY = os.getenv("NASA_MAP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OW_KEY = os.getenv("OW_KEY")
GOOGLE_SHEETS_CREDS_STR = os.getenv("GOOGLE_SHEETS_CREDS")

##================================================================ GOOGLE SHEETS LOGIC
def save_to_sheets(data_row):
    try:
        # 1. Lấy chuỗi JSON từ Secret (Dữ liệu lúc này đang là String)
        creds_json_str = os.getenv("GOOGLE_SHEETS_CREDS")
        
        if not creds_json_str:
            print("❌ Lỗi: Không tìm thấy GOOGLE_SHEETS_CREDS trong Secrets")
            return

        # 2. Chuyển chuỗi String thành Dictionary (Cực kỳ quan trọng)
        creds_info = json.loads(creds_json_str)
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 3. Sử dụng đúng hàm from_json_keyfile_dict với biến đã convert
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # Mở file Sheets
        sheet = client.open("2.NhatkythongbaoNPAPCFW2026").sheet1
        sheet.append_row(data_row)
        print("✅ Đã ghi nhật ký thành công.")
        
    except json.JSONDecodeError:
        print("❌ Lỗi: Định dạng JSON trong Secret GOOGLE_SHEETS_CREDS không hợp lệ.")
    except Exception as e:
        print(f"❌ Lỗi ghi Sheets: {e}")

##================================================================ HELPER FUNCTIONS
def get_location_name(lat, lon):
    try:
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OW_KEY}"
        response = requests.get(url)
        res = response.json()
        if response.status_code == 200 and len(res) > 0:
            location = res[0]
            names = location.get('local_names', {})
            name_vi = names.get('vi', location.get('name', ''))
            state = location.get('state', '')
            tinh_thanh = {
                "Gia Lai Province": "Tỉnh Gia Lai",
                "Kon Tum Province": "Tỉnh Kon Tum",
                "Dak Lak Province": "Tỉnh Đắk Lắk",
                "Dak Nong Province": "Tỉnh Đắk Nông",
                "Lam Dong Province": "Tỉnh Lâm Đồng"
            }
            state_vi = tinh_thanh.get(state, state)
            return f"{name_vi}, {state_vi}"
        return "Khu vực rừng núi"
    except:
        return "Tọa độ Tây Nguyên"

def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OW_KEY}&units=metric"
        res = requests.get(url).json()
        temp = res['main']['temp']
        humi = res['main']['humidity']
        wind_kmh = round(res['wind']['speed'] * 3.6, 1)
        return temp, humi, wind_kmh
    except:
        return None, None, None

def get_fire_danger(temp, humidity):
    if temp is None: return "Không xác định"
    if temp > 35 and humidity < 30: return "CẤP V (CỰC KỲ NGUY HIỂM) 🔴"
    if temp > 32 and humidity < 40: return "CẤP IV (NGUY HIỂM) 🟠"
    if temp > 28 and humidity < 50: return "CẤP III (CAO) 🟡"
    return "CẤP I - II (THẤP/TRUNG BÌNH) 🟢"

def send_telegram_alert(message, lat=None, lon=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Payload cơ bản
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML" # Đổi sang HTML để tránh lỗi ký tự đặc biệt của Markdown
    }

    # Nếu có tọa độ thì thêm nút bấm
    if lat and lon:
        # Link map rút gọn, cực kỳ an toàn
        maps_url = f"https://www.google.com/maps?q={lat},{lon}&t=k"
        nasa_url = "https://firms.modaps.eosdis.nasa.gov/map/"
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "📍 Xem Vệ Tinh", "url": maps_url},
                    {"text": "📞 Xem Website", "url": nasa_url}
                ]
            ]
        }
        payload["reply_markup"] = json.dumps(keyboard)

    response = requests.post(url, data=payload)
    
    # In ra để "bắt bệnh" nếu vẫn không nhận được
    print(f"--- THÔNG TIN TELEGRAM ---")
    print(f"Status Code: {response.status_code}")
    print(f"Phản hồi: {response.text}")
    
    
##================================================================ MAIN PROCESS
def check_for_fires():
    TEST_MODE = True # Đổi thành False để chạy thật

    if TEST_MODE:
        data_to_process = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp,daynight\n14.352,108.123,340.5,0.4,0.4,2026-04-12,08:30,N,95,6.1N,285.4,15.2,D"
    else:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_MAP_KEY}/VIIRS_SNPP_NRT/{AREA}/1"
        response = requests.get(url)
        data_to_process = response.text if response.status_code == 200 else ""

    lines = data_to_process.strip().split('\n')
    now_vn = datetime.utcnow() + timedelta(hours=7)
    gio_vn = now_vn.strftime('%H:%M:%S %d/%m/%Y')

    if len(lines) > 1:
        latest_fire = lines[1].split(',')
        lat, lon = latest_fire[0], latest_fire[1]
        conf = latest_fire[8]

        dia_danh = get_location_name(lat, lon)
        temp, humidity, wind_kmh = get_weather(lat, lon)  
        cap_bao_dong = get_fire_danger(temp, humidity)

        # 1. Ghi vào Google Sheets trước
        # Cấu trúc: Thời gian, Địa danh, Tọa độ, Nhiệt độ, Độ ẩm, Tốc độ gió, Cấp nguy cơ
        data_row = [gio_vn, dia_danh, f"{lat}, {lon}", temp, humidity, wind_kmh, cap_bao_dong]
        save_to_sheets(data_row)

        # 2. Soạn tin nhắn Telegram
        alert_msg = (
            f"🔥 **PHÁT HIỆN ĐIỂM NHIỆT KHẨN CẤP**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📍 **Địa danh: {dia_danh}\n"
            f"🌍 **Tọa độ: `{lat}, {lon}`\n\n"
            f"🔗 [Mở bản đồ vệ tinh](https://www.google.com/maps?q={lat},{lon}&t=k) \n"
            
            f"🌡 **Nhiệt độ: {temp}°C\n"
            f"💧 **Độ ẩm: {humidity}%\n"
            f"💨 **Sức gió: {wind_kmh} km/h\n"
            f"⚠️ **Dự báo: {cap_bao_dong}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏰ **Cập nhật: {gio_vn}\n"
            f"💪 **Độ tin cậy: {conf}%\n\n"

            f" Lưu ý: Nếu Cảnh báo có cháy, nhưng độ ẩm khu vực đó đang là 80% và đang có mưa, bạn có thể nghi ngờ đó là lỗi cảm biến hoặc cháy nhỏ đã bị dập tắt.\n"
            f" Đánh giá mức độ nguy hiểm: Nếu nhiệt độ là > 38°C và độ ẩm < 25%, đó là tình trạng cực kỳ khẩn cấp, cần báo động ngay lập tức. \n"
            f"☎️ Hotline báo cháy: <b> 114 </b>\n"
            f"🇻🇳 © NamPhucAPC 2026 - <b> 08888.01202 </b>"
        )
        send_telegram_alert(alert_msg, lat, lon)
    
    
    else:
        safe_msg = f"🌿 **BÁO CÁO HÀNG GIỜ**\n\n✅ Tây Nguyên hiện không có điểm nhiệt bất thường.\n⏰ {gio_vn}"
        send_telegram_alert(safe_msg)

if __name__ == "__main__":
    check_for_fires()
