import os 
# -*- coding: utf-8 -*-
# Lấy mã từ biến môi trường của GitHub
NASA_MAP_KEY = os.getenv("NASA_MAP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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
            
            # TRƯỜNG HỢP 1: CÓ ĐIỂM CHÁY (Dòng 0 là tiêu đề, từ dòng 1 là dữ liệu)
            if len(lines) > 1: 
                latest_fire = lines[1].split(',') 
                lat, lon = latest_fire[0], latest_fire[1]
                conf = latest_fire[8]
                
                alert_msg = (
                    f"🚨 *CẢNH BÁO CHÁY RỪNG TÂY NGUYÊN*\n\n"
                    f"📍 Vị trí: `{lat}, {lon}`\n"
                    f"🔥 Độ tin cậy: {conf}\n"
                    f"⏰ Cập nhật: {time.strftime('%H:%M:%S')}\n\n"
                    f"[Xem trên bản đồ](https://www.google.com/maps?q={lat},{lon})"
                )
                send_telegram_alert(alert_msg)
                print("Đã gửi cảnh báo cháy!")

            # TRƯỜNG HỢP 2: KHÔNG CÓ ĐIỂM CHÁY (Chỉ có dòng tiêu đề)
            else:
                safe_msg = (
                    f"🌿 *BÁO CÁO HÀNG GIỜ*\n\n"
                    f"✅ **Mọi thứ đều xanh tươi!**\n"
                    f"📡 Hệ thống đã quét toàn bộ Tây Nguyên và không phát hiện điểm nhiệt bất thường.\n"
                    f"⏰ Thời điểm kiểm tra: {time.strftime('%H:%M:%S')}"
                )
                send_telegram_alert(safe_msg)
                print("Đã gửi thông báo an toàn!")
                
        else:
            print(f"Lỗi kết nối NASA: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        

# Chạy kiểm tra
check_for_fires()
