# 樹莓派麥克納姆輪智慧自拍機器人 
![468435](https://github.com/user-attachments/assets/4fc84af7-bab6-49b6-89e4-fb11fe804634)


這是一個結合 **全向移動技術** 與 **AI 視覺辨識** 的智慧攝影機器人專案。透過麥克納姆輪（Mecanum Wheels）的特殊構造，它不僅能前後移動，還能進行「橫向平移（Strafing）」，完美解決了調整拍攝角度時需要反覆挪動腳架的困擾。

此外，系統整合了 OpenCV 影像辨識，具備「微笑快門」功能，當偵測到您露出笑容時，機器人會自動捕捉精彩瞬間。

-----
## 功能特色

  * **全向移動控制**：支援前進、後退、左右橫移、原地旋轉及斜向移動。
  * **Web 遠端遙控**：基於 Flask 架設網頁伺服器，無須安裝 App，手機瀏覽器即可連線控制。
  * **AI 智慧自拍**：整合 Haar Cascade 分類器，具備人臉追蹤與微笑偵測自動拍照功能。
  * **自動升降雲台**：透過電動推桿遠端調整相機高度。

-----

## 硬體材料清單

| 項目 | 說明 | 數量 |
| :--- | :--- | :--- |
| **核心控制器** | Raspberry Pi 4 Model B (建議 4GB 以上) | 1 |
| **底盤套件** | 麥克納姆輪底盤 (含 4 顆 DC 減速馬達) | 1 組 |
| **馬達驅動模組** | L298N | 3 |
| **升降模組** | 12V 電動推桿 (行程 600mm 或依需求) | 1 |
| **電源供應** | 18650 鋰電池 (串聯 3 顆，約 12V) | 1 組 |
| **穩壓模組** | 降壓模組 (12V 轉 5V 給樹莓派供電) | 1 |
| **影像裝置** | 智慧型手機 (作為 IP Camera) | 1 |
| **其他耗材** | 杜邦線、麵包板、壓克力板、束帶 | 若干 |

-----

## 硬體組裝與電路接線

本專案使用 GPIO BCM 編碼進行控制。請依照下表將馬達驅動板與樹莓派 GPIO 腳位連接。

### 1\. 麥克納姆輪馬達配置

麥克納姆輪的安裝方向非常重要，請確保輪子上的滾輪軸線呈現 **X 型** 排列（從上方俯視）。

**驅動模組 A (控制前輪)**：

  * **右前輪 (RF)**: ENA(PWM)=`GPIO 24`, IN1=`GPIO 25`, IN2=`GPIO 5`
  * **左前輪 (LF)**: ENB(PWM)=`GPIO 26`, IN1=`GPIO 6`, IN2=`GPIO 16`

**驅動模組 B (控制後輪)**：

  * **右後輪 (RR)**: ENA(PWM)=`GPIO 12`, IN1=`GPIO 17`, IN2=`GPIO 27`
  * **左後輪 (LR)**: ENB(PWM)=`GPIO 13`, IN1=`GPIO 22`, IN2=`GPIO 23`

### 2\. 升降推桿配置

  * **推桿馬達**: ENA(PWM)=`GPIO 18`, IN1=`GPIO 20`, IN2=`GPIO 21`

### 3\. 電源配置建議

  * **動力電源**：將 3 顆 18650 電池串聯 (12V)，直接連接至 L298N 的 12V 輸入端與電動推桿。
  * **邏輯電源**：使用降壓模組將 12V 轉為 5V/3A，透過 USB-C 或 GPIO 5V 腳位供電給 Raspberry Pi。
  * **共地 (Common Ground)**：**非常重要！** 樹莓派的 GND 必須與電池組的負極（GND）相連，否則控制訊號無效。

> **參考圖片**：
> ![S__6365192](https://github.com/user-attachments/assets/2081f793-0147-4364-ac8d-1aa5cea736af)


-----

## 軟體環境建置

請依序在 Raspberry Pi 的終端機執行以下指令，安裝所需的 Python 函式庫。

### 1\. 更新系統與安裝套件

```bash
sudo apt-get update
sudo apt-get upgrade
```

### 2\. 安裝專案依賴庫

本專案使用 Flask 架設網頁，並使用 OpenCV 進行影像處理。

```bash
pip3 install flask RPi.GPIO opencv-python numpy
```

*注意：安裝 `opencv-python` 在樹莓派上可能需要較長時間，請耐心等候。*

### 3\. 下載專案程式碼

將本專案的所有檔案（`web_car.py`, `templates/index.html` 等）下載至樹莓派的同一資料夾中。

-----

## 📝 程式碼說明與設定

在執行之前，您需要根據您的網路環境微調程式碼。

### 1\. 設定手機鏡頭 IP (IP Webcam)

本專案使用手機作為無線攝影機。請在手機上下載「IP Webcam」類型的 App，開啟伺服器後，記下畫面上的 IP 位址（例如 `192.168.1.100:8080`）。
![469072](https://github.com/user-attachments/assets/43be5f9e-64f3-4b0e-bf23-ab6aeac47e2c)
ipv4的部分
開啟 `web_car.py`，找到以下段落並修改：

```python
# web_car.py Line 13-14
PHONE_IP = "192.168.X.X"  # <--- 修改為您的手機 IP
PHONE_PORT = "8080"       # 通常預設為 8080
```

### 2\. 核心邏輯解析

  * **`web_car.py`**：主程式。負責啟動 Web Server，處理影像串流與 GPIO 控制。
      * **微笑偵測**：程式會自動下載 `haarcascade_smile.xml` 模型。當 `SMILE_MODE` 開啟時，OpenCV 會分析影像，偵測到微笑即呼叫 `save_photo()` 儲存照片。
      * **麥克納姆輪演算法**：透過 `move_motors(speed, dir_byte)` 函式，利用位元遮罩（Bitmask）同時控制 4 顆輪子的正反轉，實現全向移動。

-----

## 操作指南

### 1\. 啟動機器人

在樹莓派終端機執行主程式：

```bash
python3 web_car.py
```

若看到 `Running on http://0.0.0.0:5000/` 代表伺服器已啟動。

### 2\. 連線控制介面

確認手機或電腦與樹莓派連線至 **同一個 Wi-Fi 網路**。打開瀏覽器輸入：
`http://<樹莓派的IP>:5000`
如不知道樹莓派ip，可以在終端輸入`hostname -I`
### 3\. 介面功能介紹

  * **方向控制區**：包含前後左右（平移）、以及左旋（↺）、右旋（↻）按鈕。
  * **Height Control**：控制推桿「升高 ▲」或「降低 ▼」以調整相機視角。
  * **Snap**：手動拍照。
  * **Smile Mode**：切換 AI 模式。開啟後（按鈕變黃），當鏡頭前的人露出微笑，系統會自動拍照並儲存至樹莓派中。

-----

## 🔗 參考資料

本專案參考了以下文獻與技術文件：

1.  **Flask 視訊串流技術**：[Video Streaming with Flask](https://blog.miguelgrinberg.com/post/video-streaming-with-flask)
2.  **OpenCV 人臉辨識文件**：[OpenCV Cascade Classifier](https://docs.opencv.org/3.4/db/d28/tutorial_cascade_classifier.html)
3.  **麥克納姆輪運動學原理**：[Mecanum Wheel Kinematics - Wikipedia](https://en.wikipedia.org/wiki/Mecanum_wheel)
