# ESP32 Environment Monitor (Heltec V3 + BME680)

A comprehensive IoT environmental monitoring solution using the **Heltec WiFi Kit 32 V3** and a **BME680** sensor. The device measures temperature, humidity, pressure, and gas resistance (IAQ indicator), displays live data on the onboard OLED, and logs historical data to a self-hosted Python/Flask server.

*(Replace with a screenshot of your dashboard if available)*

## Features

* **Real-time Monitoring:** Displays Temperature, Humidity, Pressure, and Air Quality Status on the built-in OLED.
* **WiFi Manager:** No hardcoded credentials. Connects to known networks or creates a Captive Portal (`Heltec-Klima-Setup`) for configuration.
* **OTA Updates:** Update firmware wirelessly over the network.
* **NTP Time Sync:** Synchronizes time via local (`fritz.box`) or public NTP servers to display the current time.
* **Self-Hosted Dashboard:** Python Flask server stores data in SQLite and renders interactive historical charts using Chart.js.
* **Offline Capable:** Keeps measuring and displaying data even without a WiFi connection.

***

## 1. Hardware Setup

### Components

* **Heltec WiFi Kit 32 V3** (ESP32-S3)
* **BME680 Sensor** (I2C)


### Wiring (I2C)

The Heltec V3 uses a second hardware I2C bus for the external sensor to avoid conflicts with the onboard OLED.


| BME680 Pin | Heltec V3 Pin | Note |
| :-- | :-- | :-- |
| **VCC** | 3.3V | (Use 5V if your module has a voltage regulator) |
| **GND** | GND |  |
| **SDA** | GPIO **41** | Second I2C Bus |
| **SCL** | GPIO **42** | Second I2C Bus |

*(Note: Onboard OLED is hardwired to SDA 17 / SCL 18)*

***

## 2. ESP32 Firmware

### Prerequisites (Arduino IDE)

1. Add **Heltec ESP32** board support to Arduino IDE.
2. Select Board: **"WiFi Kit 32 V3"**.
3. Install the following libraries via Library Manager:

* `Adafruit BME680 Library` (by Adafruit)
* `Adafruit SSD1306` (by Adafruit)
* `Adafruit GFX Library` (by Adafruit)
* `WiFiManager` (by tzapu)
* `ESPAsyncWebServer` (by Mathieu Carbou / ESP32Async)
* `AsyncTCP` (by Mathieu Carbou / ESP32Async)


### Configuration (`config.h`)

Customize the `config.h` file before uploading:

```cpp
// --- SERVER CONFIGURATION ---
const char* SERVER_URL = "http://192.168.1.50:5000/post-data"; // Your PC IP
const char* API_KEY    = "MySecretKey"; 

// --- NTP CONFIGURATION ---
const char* NTP_SERVER_1 = "fritz.box";    // Local Router (preferred)
const char* NTP_SERVER_2 = "pool.ntp.org"; // Internet Backup
```


### Initial Setup

1. Flash the firmware via USB cable first.
2. On first boot, the device creates a WiFi Access Point named **`Heltec-Klima-Setup`**.
3. Connect with your phone (Password: `password`) and configure your home WiFi.
4. Subsequent updates can be done wirelessly via **OTA** (Over-The-Air) using the password defined in `config.h`.

***

## 3. Python Backend Server

A lightweight Flask server to collect and visualize data.

### Prerequisites

* Python 3.x
* Pip


### Installation

1. Clone this repository or copy the python files.
2. Install required packages:

```bash
pip install flask
```

3. Configure `config.py`:

```python
API_KEY = "MySecretKey" # Must match ESP32 config
DB_NAME = "sensor_data.db"
```


### Running the Server

Start the server in your terminal:

```bash
python3 server.py
```

* **Dashboard:** Open `http://localhost:5000` in your browser.
* **API Endpoint:** `http://localhost:5000/api/history`

***

## 4. Database Management

The server uses a local **SQLite** database (`sensor_data.db`). The database file is automatically created on the first start.

### Useful Commands (CLI)

You can manage the database directly from the terminal using Python one-liners. **Run these commands in the server directory.**

#### View last 5 entries

Checks if data is arriving correctly.

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); cursor = c.cursor(); cursor.execute('SELECT * FROM measurements ORDER BY id DESC LIMIT 5'); print(*cursor.fetchall(), sep='\n')"
```


#### Reset Database (Clear all data)

**Warning:** This deletes the table and resets the Auto-Increment ID counter to 1. Ideally for starting fresh.

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); c.execute('DROP TABLE IF EXISTS measurements'); c.commit(); print('Database reset complete.')"
```

*(Restart the server script afterwards to recreate the table structure)*

***

## License

This project is open source. Feel free to modify and distribute.

