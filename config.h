#ifndef CONFIG_H
#define CONFIG_H


// --- HARDWARE VARIANTS ---
// Comment out this line if you do NOT have a display!
#define USE_DISPLAY 


// --- WIFI & SERVER ---
const char* OTA_HOSTNAME = "Climate-Sensor";      
const char* OTA_PASS     = "Update1234";        
const char* SERVER_URL   = "http://192.168.0.2:5000/post-data"; 
const char* API_KEY      = "MySecretIoTKey123"; 


// --- TIME ---
const char* NTP_SERVER_1 = "fritz.box";      // Local router (preferred)
const char* NTP_SERVER_2 = "pool.ntp.org";   // Public Internet NTP
const long  GMT_OFFSET_SEC = 3600;           // Timezone offset (e.g. +1h for CET)
const int   DST_OFFSET_SEC = 3600;           // Daylight saving offset


// --- SENSOR ---
const unsigned long UPDATE_INTERVAL = 30000;    // 30 seconds
const unsigned long SEND_INTERVAL   = 300000;   // 5 minutes
const float GAS_LEVEL_GOOD = 50000.0;
const float GAS_LEVEL_OK   = 20000.0;
const float GAS_LEVEL_WARN = 10000.0;


// --- PIN DEFINITIONS ---
#ifdef USE_DISPLAY
  // --- Heltec V3 (With Display) ---
  #define PIN_OLED_SDA 17
  #define PIN_OLED_SCL 18
  #define PIN_OLED_RST 21
  #define SCREEN_WIDTH 128
  #define SCREEN_HEIGHT 64
  
  // Heltec uses 2nd I2C bus for the sensor to avoid OLED conflict
  #define PIN_BME_SDA  41
  #define PIN_BME_SCL  42
  #define BME_I2C_BUS  1  // Bus ID 1
#else
  // --- Standard ESP32 (No Display) ---
  // Adjust these pins for your board (e.g., 21/22 for standard DevKit)
  #define PIN_BME_SDA  21
  #define PIN_BME_SCL  22
  #define BME_I2C_BUS  0  // Standard Bus ID 0
#endif


#endif
