#ifndef CONFIG_H
#define CONFIG_H

// --- OTA KONFIGURATION (NEU) ---
const char* OTA_HOSTNAME = "Heltec-Klima";      // Name in der Arduino IDE
const char* OTA_PASS     = "Update1234";        // Dein Update-Passwort

// --- SERVER KONFIGURATION ---
// IP deines Python-Servers anpassen!
const char* SERVER_URL = "http://192.168.0.2:5000/post-data"; 
const char* API_KEY    = "MeinGeheimesIoTKennwort123"; 

// --- ZEIT KONFIGURATION (NEU) ---
const char* NTP_SERVER_1 = "192.168.0.1";      // 1. Wahl: Lokaler Server (z.B. Router)
const char* NTP_SERVER_2 = "pool.ntp.org";   // 2. Wahl: Internet
const long  GMT_OFFSET_SEC = 3600;           // Zeitzone: +1 Stunde (MEZ)
const int   DST_OFFSET_SEC = 3600;           // Sommerzeit: +1 Stunde (MESZ)

// --- TIMING ---
const unsigned long UPDATE_INTERVAL = 2000;    // Sensor lesen: Alle 2 Sekunden
const unsigned long SEND_INTERVAL   = 60000;  // Server Upload: Alle 5 Minuten

// --- SENSOR GRENZWERTE ---
const float GAS_LEVEL_GOOD = 50000.0;
const float GAS_LEVEL_OK   = 20000.0;
const float GAS_LEVEL_WARN = 10000.0;

// --- HARDWARE PIN DEFINITIONEN ---
// OLED (Heltec V3 Standard)
#define PIN_OLED_SDA 17
#define PIN_OLED_SCL 18
#define PIN_OLED_RST 21

// Display Größe
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// BME680 Sensor (Extern)
#define PIN_BME_SDA  41
#define PIN_BME_SCL  42

#endif
