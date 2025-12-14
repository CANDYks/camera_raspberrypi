# 樹莓派麥克納姆輪智慧自拍機器人

### 1\. 關於專案

一台結合 **全向移動 (Omnidirectional Movement)** 與 **AI 視覺辨識** 的智慧自拍機器人。它不僅可以透過網頁遠端遙控、橫向平移尋找最佳拍攝角度，還具備「自動升降」功能調整高度，並能開啟「微笑偵測模式」，當你露出笑容時自動捕捉精彩瞬間。

### 2\. 專案緣由

出遊想拍團體照總是要找路人幫忙？自拍棒的角度永遠受限？
我想打造一個「專屬攝影師」，它能像坦克一樣穿越各種地形，又能像攝影師一樣調整高低視角，最重要的是——它看懂我的笑容，不用按快門就能自動拍照。

### 3\. 專案構想

按照以下步驟，實現智慧自拍載具：

1.  **全向移動底盤**：使用麥克納姆輪，實現前後、左右橫移、原地旋轉。
2.  **升降雲台**：使用推桿 (Linear Actuator)，讓相機視角可以調整高低。
3.  **視覺中樞**：利用 OpenCV 捕捉影像，即時回傳至網頁。
4.  **智慧快門**：實作 Haar Cascade 模型，辨識人臉與微笑，自動觸發快門。
5.  **Web 控制介面**：使用 Flask 架設網頁伺服器，用手機瀏覽器即可全功能遙控。

### 4\. 所需材料

1.  **Raspberry Pi 4 Model B** (核心控制器)
2.  **麥克納姆輪底盤套件** (含 4 顆 DC 減速馬達)
3.  **L298N 馬達驅動模組 \* 2** (驅動 4 顆輪子)
4.  **電動推桿 (Linear Actuator) \* 1** (用於升降鏡頭)
5.  **18650 鋰電池組** (提供馬達 12V 強力電源)
6.  **行動電源** (獨立供電給樹莓派)
7.  **USB 網路攝影機** (或是 Pi Camera)
8.  **杜邦線、麵包板、固定束帶、壓克力板**

### 5\. 實體照片與介面

**機器人外觀**
*(請在此處貼上您完成後的機器人照片)*
`![Robot_Appearance](你的圖片連結.jpg)`

**Web 控制介面**
透過手機瀏覽器連線，具備即時影像、方向控制、升降控制與 AI 模式切換。
`![Web_Interface](image_51b547.png)`

### 6\. 電路配置 (GPIO 接腳定義)

本專案使用 BCM 編號，硬體接線如下：

**驅動模組 A (前輪)**

  * **右前輪 (RF)**: PWM=24, IN1=25, IN2=5
  * **左前輪 (LF)**: PWM=26, IN1=6, IN2=16

**驅動模組 B (後輪)**

  * **右後輪 (RR)**: PWM=12, IN1=17, IN2=27
  * **左後輪 (LR)**: PWM=13, IN1=22, IN2=23

**升降推桿 (Actuator)**

  * **推桿控制**: PWM=18, IN1=20, IN2=21 (共用或獨立驅動板)

### 7\. 程式設計、環境設置

**環境設置**
使用 Python 3 與 Flask 框架，並需安裝 OpenCV。

```bash
sudo apt-get update
pip3 install flask RPi.GPIO opencv-python numpy
```

**核心程式碼說明 (web\_car.py)**

  * **OpenCV 微笑偵測邏輯**：
    載入 `haarcascade_smile.xml`，偵測到微笑且信心度足夠時，自動儲存影像。

    ```python
    # 部分程式碼摘要
    if SMILE_MODE:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
        if len(smiles) > 0:
            save_photo(frame, "smile")
    ```

  * **麥克納姆輪控制 (全向移動)**：
    透過位元遮罩 (Bitmask) 同時控制四顆輪子的正反轉，實現橫移 (Strafing)。

    ```python
    MEC_SIDEWAYS_RIGHT = 0b01101001
    MEC_SIDEWAYS_LEFT  = 0b10010110

    def move_motors(speed, dir_byte):
        # 解析位元並輸出 GPIO 訊號給 L298N
        # ... (詳見原始碼)
    ```

  * **Flask 網頁伺服器**：
    利用 Video Streaming 技術將 OpenCV 處理過的畫面即時傳送到網頁。

    ```python
    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    ```

### 8\. Demo 影片

*(此處可放您的 YouTube 測試影片連結)*
[點擊觀看 Omni-Selfie-Bot 實測影片](https://www.google.com/search?q=https://youtu.be/%E4%BD%A0%E7%9A%84%E5%BD%B1%E7%89%87ID)

### 9\. 可以改進的地方

1.  **電源整合**：目前樹莓派與馬達分開供電，未來可設計穩壓電路統一由鋰電池供電。
2.  **人臉追蹤**：目前只能定點拍攝，未來可加入 PID 控制，讓機器人自動旋轉跟隨人臉移動。
3.  **手勢控制**：加入 MediaPipe 手勢辨識，比「5」停止移動，比「YA」自動拍照。
4.  **推桿限位**：目前推桿依靠時間控制，未來可加入極限開關 (Limit Switch) 防止過推。

### 10\. 參考資料

  * [Raspberry Pi Flask Video Streaming](https://blog.miguelgrinberg.com/post/video-streaming-with-flask)
  * [OpenCV Face Detection Documentation](https://docs.opencv.org/3.4/db/d28/tutorial_cascade_classifier.html)
  * [Mecanum Wheel Kinematics](https://en.wikipedia.org/wiki/Mecanum_wheel)
