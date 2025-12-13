import RPi.GPIO as GPIO
import time

# ==========================================
# 1. 最終確認腳位設定 (Based on your test)
# ==========================================

# --- 前輪 (Front) ---
# 右前 (Right Front)
RF_PWM_PIN = 24
RF_IN1_PIN = 25
RF_IN2_PIN = 5

# 左前 (Left Front)
LF_PWM_PIN = 26
LF_IN1_PIN = 6
LF_IN2_PIN = 16

# --- 後輪 (Rear) ---
# 右後 (Right Rear)
RR_PWM_PIN = 12
RR_IN1_PIN = 17
RR_IN2_PIN = 27

# 左後 (Left Rear)
LR_PWM_PIN = 13
LR_IN1_PIN = 22
LR_IN2_PIN = 23

# ==========================================
# 2. 麥克納姆輪動作定義 (位元遮罩)
# ==========================================
# Bit順序: [RF_IN1, RF_IN2, LF_IN1, LF_IN2, RR_IN1, RR_IN2, LR_IN1, LR_IN2]
MEC_STRAIGHT_FORWARD      = 0b10101010
MEC_STRAIGHT_BACKWARD     = 0b01010101
MEC_SIDEWAYS_RIGHT        = 0b01101001
MEC_SIDEWAYS_LEFT         = 0b10010110
MEC_ROTATE_CLOCKWISE      = 0b01100110
MEC_ROTATE_COUNTERCLOCKWISE = 0b10011001
MEC_DIAGONAL_45           = 0b00101000  # 右前斜
MEC_DIAGONAL_315          = 0b01000001  # 左前斜

# ==========================================
# 3. 初始化設定
# ==========================================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# 收集所有 Pin
all_pins = [
    RF_PWM_PIN, RF_IN1_PIN, RF_IN2_PIN,
    LF_PWM_PIN, LF_IN1_PIN, LF_IN2_PIN,
    RR_PWM_PIN, RR_IN1_PIN, RR_IN2_PIN,
    LR_PWM_PIN, LR_IN1_PIN, LR_IN2_PIN
]

for pin in all_pins:
    GPIO.setup(pin, GPIO.OUT)

# 啟動 PWM (頻率 1000Hz)
rf_pwm = GPIO.PWM(RF_PWM_PIN, 1000)
lf_pwm = GPIO.PWM(LF_PWM_PIN, 1000)
rr_pwm = GPIO.PWM(RR_PWM_PIN, 1000)
lr_pwm = GPIO.PWM(LR_PWM_PIN, 1000)

rf_pwm.start(0)
lf_pwm.start(0)
rr_pwm.start(0)
lr_pwm.start(0)

SPEED = 30 # 速度 0-100%

# ==========================================
# 4. 核心控制函式
# ==========================================
def move_motors(speed, dir_byte):
    # 解析位元並設定 GPIO
    # 右前
    GPIO.output(RF_IN1_PIN, (dir_byte >> 7) & 1)
    GPIO.output(RF_IN2_PIN, (dir_byte >> 6) & 1)
    rf_pwm.ChangeDutyCycle(speed)
    # 左前
    GPIO.output(LF_IN1_PIN, (dir_byte >> 5) & 1)
    GPIO.output(LF_IN2_PIN, (dir_byte >> 4) & 1)
    lf_pwm.ChangeDutyCycle(speed)
    # 右後
    GPIO.output(RR_IN1_PIN, (dir_byte >> 3) & 1)
    GPIO.output(RR_IN2_PIN, (dir_byte >> 2) & 1)
    rr_pwm.ChangeDutyCycle(speed)
    # 左後
    GPIO.output(LR_IN1_PIN, (dir_byte >> 1) & 1)
    GPIO.output(LR_IN2_PIN, (dir_byte >> 0) & 1)
    lr_pwm.ChangeDutyCycle(speed)

def stop_motors():
    rf_pwm.ChangeDutyCycle(0)
    lf_pwm.ChangeDutyCycle(0)
    rr_pwm.ChangeDutyCycle(0)
    lr_pwm.ChangeDutyCycle(0)

# ==========================================
# 5. 展示迴圈
# ==========================================
print("=== 全向移動測試開始 ===")
print("請將車子架高，或放在空曠地上")
time.sleep(2)

try:
    # 1. 前進
    print("動作: 前進 (Forward)")
    move_motors(SPEED, MEC_STRAIGHT_FORWARD)
    time.sleep(1.5)
    stop_motors()
    time.sleep(0.5)

    # 2. 後退
    print("動作: 後退 (Backward)")
    move_motors(SPEED, MEC_STRAIGHT_BACKWARD)
    time.sleep(1.5)
    stop_motors()
    time.sleep(0.5)

    # 3. 橫向右移 (關鍵測試)
    print("動作: 向右橫移 (Strafe Right)")
    move_motors(SPEED, MEC_SIDEWAYS_RIGHT)
    time.sleep(1.5)
    stop_motors()
    time.sleep(0.5)

    # 4. 橫向左移
    print("動作: 向左橫移 (Strafe Left)")
    move_motors(SPEED, MEC_SIDEWAYS_LEFT)
    time.sleep(1.5)
    stop_motors()
    time.sleep(0.5)
    
    # 5. 原地旋轉
    print("動作: 原地旋轉 (Rotate)")
    move_motors(SPEED, MEC_ROTATE_CLOCKWISE)
    time.sleep(1.5)
    stop_motors()

    print("測試完成！")

except KeyboardInterrupt:
    print("\n強制停止")
    stop_motors()
    GPIO.cleanup()
    print("GPIO 已釋放")