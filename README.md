
## ✨ Key Features

* **Multi-Hardware Support:** Single codebase for:
    * **Heltec WiFi Kit 32 V3** (with OLED display)
    * **ESP32-C3 SuperMini** (ultra-compact, headless)
    * **Generic ESP32 DevKits** (standard boards)
* **Multi-Sensor Support:**
    * **BME680** (Temperature, Humidity, Pressure, Gas/Air Quality)[^2]
    * **AM2301A / DHT21** (Temperature, Humidity)[^4][^5]
* **Dual Dashboard Architecture:**
    * **On-Device Dashboard:** Real-time web interface served directly from the ESP32 (accessible via local IP)
    * **Central Server Dashboard:** Historical data visualization with interactive charts (Flask + Chart.js)
* **Multi-Device Management:** Each sensor reports with unique MAC address identifier; central dashboard allows filtering by device
* **WiFi Manager:** Zero-config setup via captive portal (`Climate-Setup`) – no hardcoded credentials[^6]
* **OTA Updates:** Wirelessly update firmware over the network
* **NTP Time Sync:** Automatic time synchronization via local or public NTP servers
* **Offline Capable:** Continues measuring and displaying data without internet connection
* **Asynchronous Architecture:** Non-blocking web server ensures responsive dashboards even during measurements[^7][^8]

***

## 📦 Hardware Variants

### Variant A: Heltec WiFi Kit 32 V3 + BME680

**Features:** OLED Display (128x64), BME680 environmental sensor
**Use Case:** Standalone room monitor with live display


| BME680 Pin | Heltec V3 Pin | Notes |
| :-- | :-- | :-- |
| **VCC** | 3.3V | Power supply |
| **GND** | GND | Ground |
| **SDA** | GPIO **41** | I2C Bus 1 (avoids OLED conflict) |
| **SCL** | GPIO **42** | I2C Bus 1 |

**Config Setup:**

```cpp
#define USE_DISPLAY
#define USE_BME680
```


***

### Variant B: ESP32-C3 SuperMini + AM2301A (DHT21)

**Features:** Ultra-compact (22.5×18mm), low power, RISC-V architecture[^3][^9][^1]
**Use Case:** Space-constrained installations, battery-powered projects


| AM2301A Pin | ESP32-C3 Pin | Notes |
| :-- | :-- | :-- |
| **VCC (Red)** | 3V3 or 5V | Power supply (3.3-6V supported) [^4] |
| **GND (Black)** | GND | Ground |
| **DATA (Yellow)** | GPIO **8** | Digital single-wire protocol [^10] |

**Important:** The AM2301A module typically includes an internal pull-up resistor. If using the bare sensor, add a **4.7kΩ - 10kΩ** resistor between DATA and VCC.[^10]

**Config Setup:**

```cpp
#define SENSOR_TYPE_DHT
#define DHT_PIN 8
#define DHT_TYPE DHT21
```


***

### Variant C: Generic ESP32 DevKit + BME680

**Features:** Standard development board, headless operation
**Use Case:** Cost-effective multi-room monitoring


| BME680 Pin | ESP32 Pin | Notes |
| :-- | :-- | :-- |
| **VCC** | 3.3V | Power supply |
| **GND** | GND | Ground |
| **SDA** | GPIO **21** | I2C Bus 0 (standard) |
| **SCL** | GPIO **22** | I2C Bus 0 |

**Config Setup:**

```cpp
// Leave USE_DISPLAY commented out
#define USE_BME680
```


***

## 🛠️ ESP32 Firmware Setup

### Prerequisites (Arduino IDE)

Install the following libraries via **Tools → Manage Libraries**:


| Library | Author | Purpose |
| :-- | :-- | :-- |
| `Adafruit BME680 Library` | Adafruit | BME680 sensor driver |
| `Adafruit Unified Sensor` | Adafruit | Dependency for BME680 |
| `DHT sensor library` | Adafruit | AM2301A/DHT21 driver [^4] |
| `Adafruit SSD1306` | Adafruit | OLED display driver (Heltec only) |
| `Adafruit GFX Library` | Adafruit | Graphics library (Heltec only) |
| `WiFiManager` | tzapu | Captive portal for WiFi config |
| `ESPAsyncWebServer` | me-no-dev | Asynchronous web server [^7][^6] |
| `AsyncTCP` | me-no-dev | Async TCP library for ESP32 [^7] |

**Note:** When installing `DHT sensor library`, select "Install All" when prompted for dependencies.

***

### Configuration (`config.h`)

The firmware automatically adapts based on `config.h` definitions:

#### 1. Hardware Selection

```cpp
// For Heltec V3 with display + BME680:
#define USE_DISPLAY
#define USE_BME680

// For ESP32-C3 SuperMini with DHT:
#define SENSOR_TYPE_DHT
#define DHT_PIN 8
#define DHT_TYPE DHT21

// For generic ESP32 with BME680 (no display):
#define USE_BME680
```


#### 2. Network \& Server Settings

```cpp
const char* SERVER_URL = "http://192.168.1.50:5000/post-data";
const char* API_KEY    = "MeinGeheimesIoTKennwort123"; // Must match server config
```


#### 3. Timing Configuration

```cpp
const unsigned long UPDATE_INTERVAL = 30000; // Measure every 30 seconds
const unsigned long SEND_INTERVAL   = 60000; // Upload every 60 seconds
```


***

### Initial Setup \& First Use

1. **Flash Firmware:**
    * Connect ESP32 via USB
    * Select correct board in Arduino IDE:
        * Heltec: `Heltec WiFi Kit 32 V3`
        * C3: `ESP32C3 Dev Module`
        * Generic: `ESP32 Dev Module`
    * Upload sketch
2. **WiFi Configuration:**
    * On first boot, device creates AP: **`Climate-Setup`** (Password: `password`)
    * Connect with smartphone/laptop
    * Captive portal opens automatically (or navigate to `192.168.4.1`)
    * Enter your WiFi credentials
    * Device reboots and connects
3. **Access On-Device Dashboard:**
    * Check Serial Monitor for assigned IP (e.g., `192.168.1.45`)
    * Open browser: `http://192.168.1.45`
    * View live sensor data with auto-refresh
4. **Subsequent Updates (OTA):**
    * In Arduino IDE: `Tools → Port → Network Port → [Your Device]`
    * Upload wirelessly using password from `config.h`

***

## 🖥️ Python Backend Server

### Installation

1. Clone repository:
```bash
git clone <your-repo-url>
cd <repo-folder>
```

2. Install dependencies:
```bash
pip install flask
```

3. Configure `config.py`:
```python
API_KEY = "MeinGeheimesIoTKennwort123"  # Must match ESP32
DB_NAME = "klima.db"
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000
TIME_FORMAT_12H = False  # Set True for US time format
```


### Running the Server

```bash
python3 server.py
```

* **Central Dashboard:** `http://localhost:5000`
* **Device Selector:** Dropdown menu to filter by sensor MAC address
* **Time Ranges:** 1 Hour / 24 Hours / 7 Days / 30 Days
* **API Endpoints:**
    * `GET /api/history?range=day&device_id=XX:XX:XX:XX:XX:XX` - Filtered historical data
    * `GET /api/devices` - List of all registered sensors
    * `POST /post-data` - Data ingestion endpoint (used by ESP32)

***

## 📊 Multi-Sensor Management

### How It Works

1. **Device Identification:** Each ESP32 reports its MAC address as `device_id` in every upload
2. **Database Structure:** `measurements` table includes `device_id` column for filtering
3. **Dashboard Filtering:** Dropdown menu shows all active sensors; select one to view its data
4. **Automatic Discovery:** New devices appear in the dropdown as soon as they upload their first measurement

### Database Schema

```sql
CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    device_id TEXT,           -- MAC address (e.g., "AA:BB:CC:DD:EE:FF")
    temperature REAL,
    humidity REAL,
    pressure REAL,            -- 0 for DHT sensors
    gas_resistance REAL       -- 0 for DHT sensors
);
```


***

## 🔧 Database Management

### Useful Commands

**View last 5 entries (with device IDs):**

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); cursor = c.cursor(); cursor.execute('SELECT timestamp, device_id, temperature, humidity FROM measurements ORDER BY id DESC LIMIT 5'); print(*cursor.fetchall(), sep='\n')"
```

**List all registered devices:**

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); cursor = c.cursor(); cursor.execute('SELECT DISTINCT device_id FROM measurements'); print(*cursor.fetchall(), sep='\n')"
```

**Reset database (clears all data):**

```bash
python3 -c "import sqlite3, config; c = sqlite3.connect(config.DB_NAME); c.execute('DROP TABLE IF EXISTS measurements'); c.commit(); print('Database reset complete.')"
```

**Export to CSV:**

```bash
sqlite3 -header -csv klima.db "SELECT * FROM measurements" > export.csv
```


***

## 🎨 Dashboard Features

### On-Device Dashboard (ESP32)

* Live sensor values with color-coded cards
* Air quality status indicator (for BME680)
* Device MAC address display
* WiFi signal strength (RSSI)
* Auto-refresh every 2 seconds
* Dark theme optimized for OLED displays


### Central Server Dashboard (Flask)

* Interactive Chart.js time-series graphs
* Temperature, humidity, pressure, air quality trends
* Multi-device selector dropdown
* Responsive design for mobile/desktop
* Configurable time ranges with data aggregation for long periods
* 12h/24h time format support

***

## 🔐 Security Notes

* **API Key:** Change default `API_KEY` in both `config.h` and `config.py` before deployment
* **OTA Password:** Update `OTA_PASS` in `config.h` to prevent unauthorized firmware updates
* **Network Exposure:** Server binds to `0.0.0.0` by default – restrict via firewall if needed

***

## 📝 Troubleshooting

**"DHT.h: No such file or directory"**
→ Install `DHT sensor library` by Adafruit via Library Manager

**ESP32-C3 not showing display output**
→ Correct behavior – C3 variant has no display. Access dashboard via IP address

**BME680 shows 0 values on C3**
→ Correct behavior – C3 uses DHT sensor. Pressure/Gas fields are dummy values

**Server returns 403 "Invalid API Key"**
→ Ensure `API_KEY` matches exactly in `config.h` and `config.py`

**OTA not found in Arduino IDE**
→ Wait 30 seconds after boot, refresh network ports list

***

## 📜 License

Open Source. Free to use, modify, and distribute.

***

## 🙏 Credits

Built with the following third-party libraries:

* **Adafruit Sensor Libraries** – BME680, DHT, SSD1306, GFX (MIT License)
* **WiFiManager** by tzapu (MIT License)
* **ESPAsyncWebServer** by me-no-dev (LGPL 2.1)
* **AsyncTCP** by me-no-dev (LGPL 2.1)
* **Flask** – Python web framework (BSD-3-Clause)
* **Chart.js** – JavaScript charting library (MIT License)


### example images
<img width="1080" height="1034" alt="shot_12-01-2026_003" src="https://github.com/user-attachments/assets/7a0b6487-864c-4fdc-a865-8dbc3675fa0b" />

<img width="900" height="326" alt="shot_12-01-2026_004" src="https://github.com/user-attachments/assets/772b538b-42ad-40af-b26f-89b1b28e2dd4" />

<img width="925" height="166" alt="shot_12-01-2026_005" src="https://github.com/user-attachments/assets/9c7ba54b-4381-4e0c-b468-6643fdbf9f72" />



Hardware documentation references:

* ESP32-C3 SuperMini pinout[^9][^1][^3]
* AM2301A/DHT21 specifications[^5][^4][^10]
<span style="display:none">[^11][^12][^13][^14][^15]</span>

<div align="center">⁂</div>

[^1]: https://www.espboards.dev/esp32/esp32-c3-super-mini/

[^2]: https://github.com/sidharthmohannair/Tutorial-ESP32-C3-Super-Mini

[^3]: https://mischianti.org/esp32-c3-super-mini-high-resolution-pinout-datasheet-and-specs/

[^4]: https://www.hellasdigital.gr/electronics/sensors/temperature-sensors/dht21-am2301a-digital-temperature-humidity-sensor-module-with-sht11-sht15-for-arduino/?sl=en

[^5]: https://hobbycomponents.com/sensors/840-dht21-am2301-temperature-humidity-sensor

[^6]: https://github.com/me-no-dev/ESPAsyncWebServer

[^7]: https://github.com/arjenhiemstra/ESPAsyncWebServer

[^8]: https://github.com/me-no-dev/ESPAsyncWebServer/blob/master/library.json

[^9]: https://www.studiopieters.nl/esp32-c3-super-mini-pinout/

[^10]: https://www.espboards.dev/sensors/dht21/

[^11]: https://randomnerdtutorials.com/getting-started-esp32-c3-super-mini/

[^12]: https://forum.arduino.cc/t/esp32-c3-supermini-pinout/1189850

[^13]: https://www.sudo.is/docs/esphome/boards/esp32c3supermini/

[^14]: https://docs.cirkitdesigner.com/component/eafd4036-104c-43c2-b73d-1a42eae22d03/esp32-c3-supermini

[^15]: https://www.roboter-bausatz.de/p/am2301-dht21-digitaler-temperatursensor

