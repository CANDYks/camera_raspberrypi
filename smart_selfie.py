import cv2
import mediapipe as mp
import time
import requests
import numpy as np

# ==========================================
# 1. 設定區 (請修改成您手機顯示的 IP)
# ==========================================
PHONE_IP = "10.214.65.25"  # <--- 請一定要改成手機 App 上顯示的 IP
PHONE_PORT = "8080"
URL_VIDEO = f"http://{PHONE_IP}:{PHONE_PORT}/video"
URL_SNAP  = f"http://{PHONE_IP}:{PHONE_PORT}/photo_save_only.jpg"

# ==========================================
# 2. 初始化手勢辨識器 (MediaPipe)
# ==========================================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# ==========================================
# 3. 輔助函式：判斷是否比 YA
# ==========================================
def is_victory_gesture(hand_landmarks):
    # 取得指尖與指節的座標
    # 8: 食指尖, 6: 食指根
    # 12: 中指尖, 10: 中指根
    # 16: 無名指尖, 14: 無名指根
    # 20: 小指尖, 18: 小指根
    
    tips = [8, 12, 16, 20]
    pip = [6, 10, 14, 18]
    fingers_up = []

    # 判斷每一根手指是否伸直 (指尖 y 座標 < 指節 y 座標)
    # 注意：影像座標左上角是 (0,0)，越往下 y 越大
    for t, p in zip(tips, pip):
        if hand_landmarks.landmark[t].y < hand_landmarks.landmark[p].y:
            fingers_up.append(True)
        else:
            fingers_up.append(False)
            
    # 比 YA 的邏輯：食指(0)與中指(1)伸直，無名指(2)與小指(3)彎曲
    if fingers_up[0] and fingers_up[1] and not fingers_up[2] and not fingers_up[3]:
        return True
    return False

# ==========================================
# 4. 主程式
# ==========================================
print(f"正在連線至手機鏡頭: {URL_VIDEO} ...")
cap = cv2.VideoCapture(URL_VIDEO)

if not cap.isOpened():
    print("無法連線！請檢查手機 IP 是否正確，或防火牆是否阻擋。")
    exit()

# 拍照倒數變數
countdown_start = 0
is_counting_down = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("畫面中斷")
        break

    # 鏡頭畫面翻轉 (像鏡子一樣)
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    # 轉成 RGB 給 MediaPipe 用
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # 畫出偵測到的手
    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            # 判斷手勢
            if is_victory_gesture(hand_lms):
                if not is_counting_down:
                    print("偵測到 YA 手勢！開始倒數...")
                    is_counting_down = True
                    countdown_start = time.time()

    # 處理倒數邏輯
    if is_counting_down:
        elapsed = time.time() - countdown_start
        remaining = 3 - int(elapsed)
        
        # 在畫面上顯示倒數數字
        cv2.putText(frame, str(remaining), (w//2-50, h//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
        
        if elapsed > 3:
            # 時間到，拍照！
            print("卡嚓！傳送拍照指令...")
            try:
                # 這是 IP Webcam 的 API，會讓手機直接存照片到相簿
                requests.get(URL_SNAP, timeout=2)
                print("照片已儲存在手機相簿中！")
            except Exception as e:
                print(f"拍照失敗: {e}")
            
            # 拍完後冷卻一下，避免連續連拍
            cv2.putText(frame, "Saved!", (w//2-100, h//2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
            cv2.imshow("Selfie Bot View", frame)
            cv2.waitKey(2000) # 暫停 2 秒
            is_counting_down = False

    # 顯示畫面
    cv2.imshow("Selfie Bot View", frame)

    # 按 'q' 離開
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()