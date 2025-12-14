from flask import Flask, render_template, Response, request
import RPi.GPIO as GPIO
import cv2
import numpy as np
import os
import urllib.request
import time

app = Flask(__name__)

# ==========================================
# 0. 手機鏡頭設定 (請確認這是您的手機 IP)
# ==========================================
PHONE_IP = "10.132.114.29"  # <--- 這裡填手機上顯示的 IP
PHONE_PORT = "8080"        # 通常是 8080
# 設定影像來源
VIDEO_URL = f"http://{PHONE_IP}:{PHONE_PORT}/video"

# === 新增這段模型載入程式 ===
face_xml = 'haarcascade_frontalface_default.xml'
smile_xml = 'haarcascade_smile.xml'

# 自動下載模型檔
def download_cascade(filename):
    if not os.path.exists(filename):
        print(f"下載中: {filename}")
        url = f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{filename}"
        urllib.request.urlretrieve(url, filename)

download_cascade(face_xml)
download_cascade(smile_xml)

face_cascade = cv2.CascadeClassifier(face_xml)
smile_cascade = cv2.CascadeClassifier(smile_xml)

SMILE_MODE = False
last_photo_time = 0
# ===========================
# ==========================================
# 1. 腳位與 GPIO 初始化
# ==========================================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# 前輪
RF_PWM_PIN, RF_IN1_PIN, RF_IN2_PIN = 24, 25, 5
LF_PWM_PIN, LF_IN1_PIN, LF_IN2_PIN = 26, 6, 16
# 後輪
RR_PWM_PIN, RR_IN1_PIN, RR_IN2_PIN = 12, 17, 27
LR_PWM_PIN, LR_IN1_PIN, LR_IN2_PIN = 13, 22, 23
# 推桿
ACT_PWM_PIN, ACT_IN1_PIN, ACT_IN2_PIN = 18, 20, 21

all_pins = [
    RF_PWM_PIN, RF_IN1_PIN, RF_IN2_PIN,
    LF_PWM_PIN, LF_IN1_PIN, LF_IN2_PIN,
    RR_PWM_PIN, RR_IN1_PIN, RR_IN2_PIN,
    LR_PWM_PIN, LR_IN1_PIN, LR_IN2_PIN,
    ACT_PWM_PIN, ACT_IN1_PIN, ACT_IN2_PIN
]

for pin in all_pins:
    GPIO.setup(pin, GPIO.OUT)

# PWM 設定
rf_pwm = GPIO.PWM(RF_PWM_PIN, 1000)
lf_pwm = GPIO.PWM(LF_PWM_PIN, 1000)
rr_pwm = GPIO.PWM(RR_PWM_PIN, 1000)
lr_pwm = GPIO.PWM(LR_PWM_PIN, 1000)
act_pwm = GPIO.PWM(ACT_PWM_PIN, 1000)

for pwm in [rf_pwm, lf_pwm, rr_pwm, lr_pwm, act_pwm]:
    pwm.start(0)

SPEED = 60
ACT_SPEED = 100

# ==========================================
# 2. 動作控制函式 (省略細節，跟之前一樣)
# ==========================================
MEC_STRAIGHT_FORWARD = 0b10101010
MEC_STRAIGHT_BACKWARD = 0b01010101
MEC_SIDEWAYS_RIGHT = 0b01101001
MEC_SIDEWAYS_LEFT = 0b10010110
MEC_ROTATE_CLOCKWISE = 0b01100110
MEC_ROTATE_COUNTERCLOCKWISE = 0b10011001

def move_motors(speed, dir_byte):
    GPIO.output(RF_IN1_PIN, (dir_byte >> 7) & 1)
    GPIO.output(RF_IN2_PIN, (dir_byte >> 6) & 1)
    rf_pwm.ChangeDutyCycle(speed)
    GPIO.output(LF_IN1_PIN, (dir_byte >> 5) & 1)
    GPIO.output(LF_IN2_PIN, (dir_byte >> 4) & 1)
    lf_pwm.ChangeDutyCycle(speed)
    GPIO.output(RR_IN1_PIN, (dir_byte >> 3) & 1)
    GPIO.output(RR_IN2_PIN, (dir_byte >> 2) & 1)
    rr_pwm.ChangeDutyCycle(speed)
    GPIO.output(LR_IN1_PIN, (dir_byte >> 1) & 1)
    GPIO.output(LR_IN2_PIN, (dir_byte >> 0) & 1)
    lr_pwm.ChangeDutyCycle(speed)

def stop_motors():
    for pwm in [rf_pwm, lf_pwm, rr_pwm, lr_pwm]:
        pwm.ChangeDutyCycle(0)
        
def save_photo(frame, reason="photo"):
    filename = time.strftime(f"{reason}_%Y%m%d_%H%M%S.jpg")
    cv2.imwrite(filename, frame)
    print(f"已拍照: {filename}")

def gen_frames():
    global last_photo_time, SMILE_MODE
    cap = cv2.VideoCapture(VIDEO_URL)
    while True:
        success, frame = cap.read()
        if not success:
            cap.release()
            cap = cv2.VideoCapture(VIDEO_URL)
            continue
            
        frame = cv2.resize(frame, (640, 480))
        
        # 微笑偵測邏輯
        if SMILE_MODE:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                roi_gray = gray[y:y+h, x:x+w]
                smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
                if len(smiles) > 0 and (time.time() - last_photo_time > 3):
                    cv2.putText(frame, "SMILE!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    save_photo(frame, "smile")
                    last_photo_time = time.time()

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def actuator_up():
    GPIO.output(ACT_IN1_PIN, GPIO.HIGH)
    GPIO.output(ACT_IN2_PIN, GPIO.LOW)
    act_pwm.ChangeDutyCycle(ACT_SPEED)

def actuator_down():
    GPIO.output(ACT_IN1_PIN, GPIO.LOW)
    GPIO.output(ACT_IN2_PIN, GPIO.HIGH)
    act_pwm.ChangeDutyCycle(ACT_SPEED)

def actuator_stop():
    act_pwm.ChangeDutyCycle(0)
    GPIO.output(ACT_IN1_PIN, GPIO.LOW)
    GPIO.output(ACT_IN2_PIN, GPIO.LOW)

# ==========================================
# 3. 網頁路由 (Web Routes)
# ==========================================
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/action/<cmd>')
def action(cmd):
    # 這裡跟之前一模一樣
    global SMILE_MODE
    if cmd == 'snap':
        cap = cv2.VideoCapture(VIDEO_URL)
        ret, frame = cap.read()
        if ret: save_photo(frame, "manual")
        return "Snapped"
    elif cmd == 'toggle_smile':
        SMILE_MODE = not SMILE_MODE
        return "On" if SMILE_MODE else "Off"
    elif cmd == 'forward': move_motors(SPEED, MEC_STRAIGHT_FORWARD)
    elif cmd == 'backward': move_motors(SPEED, MEC_STRAIGHT_BACKWARD)
    elif cmd == 'left': move_motors(SPEED, MEC_SIDEWAYS_LEFT)
    elif cmd == 'right': move_motors(SPEED, MEC_SIDEWAYS_RIGHT)
    elif cmd == 'rotate_cw': move_motors(SPEED, MEC_ROTATE_CLOCKWISE)
    elif cmd == 'rotate_ccw': move_motors(SPEED, MEC_ROTATE_COUNTERCLOCKWISE)
    elif cmd == 'stop': stop_motors()
    elif cmd == 'up': actuator_up()
    elif cmd == 'down': actuator_down()
    elif cmd == 'act_stop': actuator_stop()
    return "OK"

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        stop_motors()
        actuator_stop()
        GPIO.cleanup()