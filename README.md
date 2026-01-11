<img width="1111" height="953" alt="shot_11-01-2026_004" src="https://github.com/user-attachments/assets/6614a44b-57d3-4ec5-a5a2-6682ae32aef6" />


# ESP32 Environment Monitor (IoT)

A versatile IoT environmental monitoring solution supporting both **Heltec WiFi Kit 32 V3** (with OLED) and standard **ESP32 DevKits** (headless). The device measures temperature, humidity, pressure, and gas resistance using a **BME680** sensor and logs historical data to a self-hosted Python/Flask server.

## Features

* **Dual Hardware Support:** Single codebase works for Heltec V3 (display enabled) and generic ESP32s (display disabled).
* **Real-time Monitoring:** Live data on OLED (if available) or via Web Dashboard.
* **WiFi Manager:** No hardcoded credentials. Connects to known networks or creates a Captive Portal (`Klima-Setup`) for configuration.
* **OTA Updates:** Update firmware wirelessly over the network.
* **NTP Time Sync:** Synchronizes time via local (`fritz.box`) or public NTP servers.
* **Self-Hosted Dashboard:** Python Flask server stores data in SQLite and renders interactive historical charts using Chart.js.
* **Offline Capable:** Keeps measuring and displaying data even without a WiFi connection.

***

## 1. Hardware Setup

### Variant A: Heltec WiFi Kit 32 V3

Uses two separate I2C buses to avoid conflicts with the internal OLED.


| BME680 Pin | Heltec V3 Pin | Note |
| :-- | :-- | :-- |
| **VCC** | 3.3V / 5V | Depends on module |
| **GND** | GND |  |
| **SDA** | GPIO **41** | Second I2C Bus |
| **SCL** | GPIO **42** | Second I2C Bus |

### Variant B: Standard ESP32 (DevKit)

Uses the standard I2C bus.


| BME680 Pin | ESP32 Pin | Note |
| :-- | :-- | :-- |
| **VCC** | 3.3V / 5V |  |
| **GND** | GND |  |
| **SDA** | GPIO **21** | Standard I2C |
| **SCL** | GPIO **22** | Standard I2C |


***

## 2. ESP32 Firmware

### Prerequisites (Arduino IDE)

1. Install the following libraries via Library Manager:
    * `Adafruit BME680 Library` (Adafruit)
    * `Adafruit SSD1306` \& `Adafruit GFX` (Adafruit)
    * `WiFiManager` (tzapu)
    * `ESPAsyncWebServer` (Mathieu Carbou / ESP32Async)
    * `AsyncTCP` (Mathieu Carbou / ESP32Async)

### Configuration (`config.h`)

This is the main control file.

1. **Select Hardware:** Uncomment `USE_DISPLAY` for Heltec V3, or comment it out for generic ESP32.

```cpp
#define USE_DISPLAY // Comment out for headless ESP32
```

2. **Server Settings:**

```cpp
const char* SERVER_URL = "http://192.168.1.50:5000/post-data";
const char* API_KEY    = "MySecretKey";
```


### Initial Setup

1. Flash the firmware via USB.
2. On first boot, connect to WiFi AP **`Klima-Setup`** (Password: `password`) to configure your network.
3. Subsequent updates can be done via **OTA** (Over-The-Air) using the password defined in `config.h`.

***

## 3. Python Backend Server

A lightweight Flask server to collect and visualize data.

### Prerequisites

* Python 3.x
* Pip


### Installation

1. Clone this repository.
2. Install Flask:

```bash
pip install flask
```

3. Configure `config.py`:

```python
API_KEY = "MySecretKey" # Must match ESP32 config
DB_NAME = "sensor_data.db"
```


### Running the Server

```bash
python3 server.py
```

* **Dashboard:** Open `http://localhost:5000`
* **API Endpoint:** `http://localhost:5000/api/history`

***

## 4. Database Management

The server uses a local **SQLite** database (`sensor_data.db`).

### Useful Commands (CLI)

**View last 5 entries:**

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); cursor = c.cursor(); cursor.execute('SELECT * FROM measurements ORDER BY id DESC LIMIT 5'); print(*cursor.fetchall(), sep='\n')"
```

**Reset Database (Clear all data):**

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); c.execute('DROP TABLE IF EXISTS measurements'); c.commit(); print('Database reset complete.')"
```


***

## License

Open Source. Feel free to modify and distribute.

