import cv2
import time
import requests
import os
import urllib.request

# ==========================================
# 1. 設定區
# ==========================================
PHONE_IP = "10.132.114.29"  # <--- 請確認 IP
PHONE_PORT = "8080"
URL_VIDEO = f"http://{PHONE_IP}:{PHONE_PORT}/video"
URL_PHOTO = f"http://{PHONE_IP}:{PHONE_PORT}/photo.jpg"
SAVE_DIR = os.getcwd()

# ==========================================
# 2. 下載 OpenCV 的特徵模型檔 (如果沒有的話)
# ==========================================
face_xml = 'haarcascade_frontalface_default.xml'
smile_xml = 'haarcascade_smile.xml'

def download_cascade(filename):
    if not os.path.exists(filename):
        print(f"下載模型檔: {filename}...")
        url = f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{filename}"
        urllib.request.urlretrieve(url, filename)

download_cascade(face_xml)
download_cascade(smile_xml)

# 載入模型
face_cascade = cv2.CascadeClassifier(face_xml)
smile_cascade = cv2.CascadeClassifier(smile_xml)

# ==========================================
# 3. 主程式
# ==========================================
print("=== 微笑自拍啟動 ===")
print("請看鏡頭並微笑 :D")

cap = cv2.VideoCapture(URL_VIDEO)
state = "WAITING"
smile_frames = 0
countdown_start = 0

while True:
    try:
        ret, frame = cap.read()
        if not ret:
            time.sleep(1)
            cap = cv2.VideoCapture(URL_VIDEO)
            continue

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 轉灰階加速

        # 1. 偵測人臉
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        current_smile_detected = False

        for (x, y, w, h) in faces:
            # 畫出人臉框
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # 只在「人臉區域內」找微笑 (節省效能)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]

            # 調整 scaleFactor 和 minNeighbors 可以改變靈敏度
            # minNeighbors 越大越嚴格 (不容易誤判，但也比較難觸發)
            smiles = smile_cascade.detectMultiScale(roi_gray, 2.0, 7)

            for (sx, sy, sw, sh) in smiles:
                cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), (0, 255, 0), 2)
                current_smile_detected = True

        # ==========================
        # 狀態機邏輯
        # ==========================
        if state == "WAITING":
            if current_smile_detected:
                smile_frames += 1
                cv2.putText(frame, "Smiling!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 連續笑 15 幀 (約 0.5 ~ 1 秒) 才算數
                if smile_frames > 15:
                    print("偵測到微笑！")
                    state = "COUNTDOWN"
                    countdown_start = time.time()
                    smile_frames = 0
            else:
                smile_frames = 0

        elif state == "COUNTDOWN":
            timer = 3 - int(time.time() - countdown_start)
            cv2.putText(frame, str(timer), (280, 240), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
            
            if timer <= 0:
                print(">>> 拍照！")
                try:
                    resp = requests.get(URL_PHOTO, timeout=10)
                    if resp.status_code == 200:
                        filename = time.strftime("smile_%H%M%S.jpg")
                        with open(filename, 'wb') as f:
                            f.write(resp.content)
                        cv2.putText(frame, "Saved!", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                except:
                    pass
                time.sleep(2)
                state = "WAITING"

        cv2.imshow("Smile Cam", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print(e)
        break

cap.release()
cv2.destroyAllWindows()