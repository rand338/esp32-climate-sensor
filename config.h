#ifndef CONFIG_H
#define CONFIG_H

// ==========================================
//           HARDWARE AUSWAHL
// ==========================================

// --- BOARD & SENSOR WAHL ---
// Aktivieren für Heltec V3 mit OLED & BME680
 #define USE_DISPLAY     
 #define USE_BME680      

// Aktivieren für ESP32-C3 SuperMini mit AM2301A (DHT)
//#define SENSOR_TYPE_DHT   
//#define DHT_PIN 8         // GPIO 8 am C3 SuperMini
//#define DHT_TYPE DHT21    // AM2301 = DHT21

// ==========================================
//           NETZWERK & SERVER
// ==========================================

const char* OTA_HOSTNAME = "Klima-Sensor"; // Name angepasst für C3      
const char* OTA_PASS     = "Update1234";        
const char* SERVER_URL   = "http://192.168.0.2:5000/post-data"; 
const char* API_KEY      = "MeinGeheimesIoTKennwort123"; 

// ==========================================
//                ZEIT
// ==========================================
const char* NTP_SERVER_1 = "fritz.box";
const char* NTP_SERVER_2 = "pool.ntp.org";
const long  GMT_OFFSET_SEC = 3600;
const int   DST_OFFSET_SEC = 3600;

// ==========================================
//           MESSEN & SENDEN
// ==========================================
const unsigned long UPDATE_INTERVAL = 30000;   // Messen alle 30 sek
const unsigned long SEND_INTERVAL   = 60000;   // Senden alle 60 sek

// Grenzwerte (Nur relevant für BME680 Gas-Sensor)
const float GAS_LEVEL_GOOD = 50000.0;
const float GAS_LEVEL_OK   = 20000.0;
const float GAS_LEVEL_WARN = 10000.0;

// ==========================================
//           PIN DEFINITIONEN
// ==========================================

#if defined(USE_DISPLAY)
  // --- Heltec V3 (Mit Display) ---
  #define PIN_OLED_SDA 17
  #define PIN_OLED_SCL 18
  #define PIN_OLED_RST 21
  #define SCREEN_WIDTH 128
  #define SCREEN_HEIGHT 64
  
  // Heltec nutzt 2. Bus für Sensor
  #define PIN_BME_SDA  41
  #define PIN_BME_SCL  42
  #define BME_I2C_BUS  1 
#elif defined(USE_BME680)
  // --- Standard ESP32 + BME680 (Ohne Display) ---
  #define PIN_BME_SDA  21
  #define PIN_BME_SCL  22
  #define BME_I2C_BUS  0 
#endif

// Für DHT brauchen wir keine I2C Pins definieren, 
// da Pin 8 oben schon definiert ist.

#endif
