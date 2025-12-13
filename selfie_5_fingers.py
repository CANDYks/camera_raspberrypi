import cv2
import numpy as np
import time
import requests
import math
import os

# ==========================================
# 1. 設定區 (請確認 IP)
# ==========================================
PHONE_IP = "10.132.114.29"   # <--- 請確認手機 IP
PHONE_PORT = "8080"
URL_VIDEO = f"http://{PHONE_IP}:{PHONE_PORT}/video"
URL_PHOTO = f"http://{PHONE_IP}:{PHONE_PORT}/photo.jpg" # 讀取照片檔的網址

# 儲存路徑 (存到目前資料夾)
SAVE_DIR = os.getcwd()

# ==========================================
# 2. 膚色偵測參數 (最關鍵！)
# ==========================================
# 如果一直亂偵測，請嘗試調整這裡
# H: 色相 (0-180), S: 飽和度 (0-255), V: 亮度 (0-255)
# 建議在光線充足的地方測試
lower_skin = np.array([0, 40, 60], dtype=np.uint8)
upper_skin = np.array([20, 255, 255], dtype=np.uint8)

# ==========================================
# 3. 核心運算：數手指
# ==========================================
def count_fingers(contour, frame_debug):
    # 計算凸包 (Convex Hull)
    hull = cv2.convexHull(contour, returnPoints=False)
    
    if len(hull) > 3:
        # 找出凸包缺口 (Defects)，也就是指縫
        defects = cv2.convexityDefects(contour, hull)
        
        if defects is None:
            return 0
            
        count = 0
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(contour[s][0])
            end = tuple(contour[e][0])
            far = tuple(contour[f][0])
            
            # 利用三角形三邊長求角度 (餘弦定理)
            a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
            c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
            
            # 計算手指夾角
            angle = math.acos((b**2 + c**2 - a**2) / (2*b*c)) * 57
            
            # 如果角度小於 90 度，視為一個指縫
            if angle <= 90:
                count += 1
                # 畫出指縫 (紅色點)
                cv2.circle(frame_debug, far, 5, [0, 0, 255], -1)
        
        # 手指數量 = 指縫數 + 1
        return count + 1
    return 0

# ==========================================
# 4. 主程式
# ==========================================
print("=== 智慧自拍機器人 2.0 ===")
print("1. 請將手放入綠色框框內")
print("2. 張開 5 根手指 (比 High-Five)")
print("3. 維持 1 秒後開始倒數")

cap = cv2.VideoCapture(URL_VIDEO)

# 狀態變數
state = "WAITING"   # 狀態: WAITING (等待), COUNTDOWN (倒數), SAVING (存檔)
stable_frames = 0   # 穩定偵測計數器
countdown_start = 0 # 倒數開始時間

while True:
    try:
        ret, frame = cap.read()
        if not ret:
            print("無法讀取畫面，重試中...")
            time.sleep(1)
            cap = cv2.VideoCapture(URL_VIDEO)
            continue

        # 畫面翻轉與縮放
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        
        # 定義偵測區域 (ROI) - 綠色框框
        cv2.rectangle(frame, (350, 50), (600, 300), (0, 255, 0), 2)
        roi = frame[50:300, 350:600]
        
        # 膚色過濾
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # 消除雜訊 (很重要)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=4)
        mask = cv2.GaussianBlur(mask, (5, 5), 100)
        
        # 找輪廓
        try:
            # 針對舊版 OpenCV (3.x)
            _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        except ValueError:
            # 針對新版 OpenCV (4.x)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        fingers = 0
        if len(contours) > 0:
            # 找最大的輪廓
            max_contour = max(contours, key=cv2.contourArea)
            
            # 只有面積夠大才算 (過濾雜訊)
            if cv2.contourArea(max_contour) > 2000:
                cv2.drawContours(roi, [max_contour], -1, (0, 255, 255), 2)
                fingers = count_fingers(max_contour, roi)
                
                # 顯示手指數量
                cv2.putText(frame, f"Fingers: {fingers}", (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # 顯示除錯視窗 (黑白)
        cv2.imshow("Debug Mask", mask)

        # ==========================
        # 狀態機邏輯
        # ==========================
        if state == "WAITING":
            # 條件：偵測到 5 根手指 (或 4 個指縫)
            if fingers >= 5:
                stable_frames += 1
                # 進度條效果
                cv2.rectangle(frame, (200, 400), (200 + stable_frames * 10, 420), (0, 255, 0), -1)
                
                # 如果連續 20 幀 (約 1 秒) 都偵測到 5 指，開始倒數
                if stable_frames > 20:
                    print("偵測到 5 指！開始倒數...")
                    state = "COUNTDOWN"
                    countdown_start = time.time()
                    stable_frames = 0
            else:
                stable_frames = 0 # 手指不對就重置，防止誤判

        elif state == "COUNTDOWN":
            elapsed = time.time() - countdown_start
            timer = 5 - int(elapsed) # 倒數 5 秒
            
            # 顯示大大的數字
            cv2.putText(frame, str(timer), (280, 240), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
            
            if timer <= 0:
                state = "SAVING"

        elif state == "SAVING":
            print(">>> 拍照中...")
            cv2.putText(frame, "Say Cheese!", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
            cv2.imshow("Selfie Bot", frame)
            cv2.waitKey(1)
            
            try:
                # 1. 從手機下載照片
                resp = requests.get(URL_PHOTO, timeout=10)
                
                if resp.status_code == 200:
                    # 2. 產生檔名 (依時間)
                    filename = time.strftime("pi_selfie_%Y%m%d_%H%M%S.jpg")
                    filepath = os.path.join(SAVE_DIR, filename)
                    
                    # 3. 寫入樹莓派硬碟
                    with open(filepath, 'wb') as f:
                        f.write(resp.content)
                    
                    print(f"✅ 照片已存檔: {filepath}")
                    cv2.putText(frame, "Saved to Pi!", (180, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    print("❌ 下載失敗，手機回應錯誤碼")

            except Exception as e:
                print(f"❌ 連線錯誤: {e}")
            
            time.sleep(2) # 顯示結果 2 秒
            state = "WAITING"

        cv2.imshow("Selfie Bot", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    except Exception as e:
        print(f"發生錯誤: {e}")
        break

cap.release()
cv2.destroyAllWindows()