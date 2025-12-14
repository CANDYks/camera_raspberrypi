import RPi.GPIO as GPIO
import time

# ==========================
# 腳位設定
# ==========================
ACT_PWM_PIN = 18
ACT_IN1_PIN = 20
ACT_IN2_PIN = 21

# 初始化
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(ACT_PWM_PIN, GPIO.OUT)
GPIO.setup(ACT_IN1_PIN, GPIO.OUT)
GPIO.setup(ACT_IN2_PIN, GPIO.OUT)

# 啟動 PWM
act_pwm = GPIO.PWM(ACT_PWM_PIN, 1000)
act_pwm.start(0)
SPEED = 100  # 推桿通常需要全力推，設 100 最保險

def extend():
    print("推桿：伸出 (UP)")
    GPIO.output(ACT_IN1_PIN, GPIO.HIGH)
    GPIO.output(ACT_IN2_PIN, GPIO.LOW)
    act_pwm.ChangeDutyCycle(SPEED)

def retract():
    print("推桿：縮回 (DOWN)")
    GPIO.output(ACT_IN1_PIN, GPIO.LOW)
    GPIO.output(ACT_IN2_PIN, GPIO.HIGH)
    act_pwm.ChangeDutyCycle(SPEED)

def stop():
    print("推桿：停止")
    GPIO.output(ACT_IN1_PIN, GPIO.LOW)
    GPIO.output(ACT_IN2_PIN, GPIO.LOW)
    act_pwm.ChangeDutyCycle(0)

# ==========================
# 測試迴圈
# ==========================
print("=== 推桿測試 ===")
print("按 'u' 伸出, 'd' 縮回, 's' 停止, 'q' 離開")

try:
    while True:
        cmd = input("指令: ")
        if cmd == 'u':
            extend()
        elif cmd == 'd':
            retract()
        elif cmd == 's':
            stop()
        elif cmd == 'q':
            stop()
            break
            
except KeyboardInterrupt:
    pass
finally:
    stop()
    GPIO.cleanup()