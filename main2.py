import os

# --- CẤU HÌNH --- # Lấy mã từ biến môi trường của GitHub
NASA_MAP_KEY = os.getenv("719970f391a4c03e8343479f97d37c6b")
TELEGRAM_TOKEN = os.getenv("8755390549:AAEMUVKGDyLKJc1XEuLRDs9iIfeBzBrhRVA")
CHAT_ID = os.getenv("1003717660062")

# Tọa độ Tây Nguyên (Bounding Box)
AREA = "107,11,110,16" 

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def check_for_fires():
    # Gọi API NASA lấy dữ liệu CSV
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_MAP_KEY}/VIIRS_SNPP_NRT/{AREA}/1"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) > 1: # Có dữ liệu (Dòng 0 là tiêu đề)
                latest_fire = lines[1].split(',') # Lấy điểm cháy mới nhất
                lat, lon = latest_fire[0], latest_fire[1]
                conf = latest_fire[8] # Độ tin cậy (Confidence)
                
                # Tạo nội dung tin nhắn theo phong cách báo chí tối giản
                alert_msg = (
                    f"🚨 *CẢNH BÁO NGUY CƠ CHÁY RỪNG KHU VỰC TÂY NGUYÊN*\n\n"
                    f"📍 Vị trí: `{lat}, {lon}`\n"
                    f"🔥 Độ tin cậy: {conf}\n"
                    f"⏰ Cập nhật: {time.strftime('%H:%M:%S')}\n\n"
                    f"[Xem trên bản đồ](https://www.google.com/maps/search/?api=1&query={lat},{lon})"
                )
                send_telegram_alert(alert_msg)
                print("Đã gửi cảnh báo tới Telegram!")
            else:
                print("Hiện tại rừng vẫn an toàn.")
    except Exception as e:
        print(f"Lỗi: {e}")

# Chạy kiểm tra
check_for_fires()