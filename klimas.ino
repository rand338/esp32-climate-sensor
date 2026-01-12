#include <WiFi.h>
#include <HTTPClient.h> 
#include <WiFiManager.h> 
#include <AsyncTCP.h>

// Fix für Konflikte zwischen ESP32 Core WebServer und AsyncWebServer
#ifdef HTTP_GET
  #undef HTTP_GET
  #undef HTTP_POST
  #undef HTTP_DELETE
  #undef HTTP_PUT
  #undef HTTP_PATCH
  #undef HTTP_HEAD
  #undef HTTP_OPTIONS
  #undef HTTP_ANY
#endif

#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include <ArduinoOTA.h>
#include "time.h" 
#include "config.h" 

// --- 1. HARDWARE MODULE ---

// A) DISPLAY
#ifdef USE_DISPLAY
  #include <Wire.h>
  #include <Adafruit_GFX.h>
  #include <Adafruit_SSD1306.h>
  Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, PIN_OLED_RST);
#endif

// B) BME680 SENSOR
#ifdef USE_BME680
  #include <Wire.h>
  #include <Adafruit_Sensor.h>
  #include "Adafruit_BME680.h"
  // Wählt Bus 0 oder 1 je nach config
  TwoWire I2C_BME = TwoWire(BME_I2C_BUS);
  Adafruit_BME680 bme(&I2C_BME);
#endif

// C) DHT SENSOR
#ifdef SENSOR_TYPE_DHT
  #include <DHT.h>
  DHT dht(DHT_PIN, DHT_TYPE);
#endif

// --- GLOBALE VARIABLEN ---
AsyncWebServer server(80);

float temp = 0.0, hum = 0.0, pres = 0.0, gas = 0.0;
String airQualityStatus = "Init..."; 
unsigned long lastSensorTime = 0;
unsigned long lastSendTime = 0;

// --- HELFER: TEXT ANZEIGEN (Display oder Serial) ---
void showText(String title, String status) {
  #ifdef USE_DISPLAY
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0,0);
    display.println(title);
    display.println(status);
    display.display();
  #else
    Serial.print("[INFO] "); Serial.print(title); Serial.print(": "); Serial.println(status);
  #endif
}

// --- HELFER: LUFTQUALITÄT BERECHNEN ---
String getAirQuality(float gasResistance) {
  // Wenn kein Gassensor da ist (z.B. DHT), geben wir "-" zurück
  #ifdef SENSOR_TYPE_DHT
    return "N/A";
  #endif

  if (gasResistance > GAS_LEVEL_GOOD) return "Top";
  else if (gasResistance > GAS_LEVEL_OK) return "Good";
  else if (gasResistance > GAS_LEVEL_WARN) return "Fair";
  else if (gasResistance > 0) return "WARNING";
  return "Init";
}

// --- HELFER: ZEIT FORMATIEREN ---
String getFormattedTime() {
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)) return "--:--";
  char timeStringBuff[6];
  strftime(timeStringBuff, sizeof(timeStringBuff), "%H:%M", &timeinfo);
  return String(timeStringBuff);
}

// --- DATEN SENDEN ---
void sendDataToServer() {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClient client;
    HTTPClient http;
    http.setTimeout(3000); 
    http.begin(client, SERVER_URL);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String mac = WiFi.macAddress();
    
    String httpRequestData = "api_key=" + String(API_KEY) 
                           + "&device_id=" + mac
                           + "&temperature=" + String(temp)
                           + "&humidity=" + String(hum)
                           + "&pressure=" + String(pres)
                           + "&gas=" + String(gas);
                           
    int code = http.POST(httpRequestData);
    if(code > 0) Serial.printf("Upload: %d\n", code);
    http.end();
  }
}

// --- WIFI MANAGER CALLBACK ---
void configModeCallback (WiFiManager *myWiFiManager) {
  Serial.println("Config Mode Start...");
  #ifdef USE_DISPLAY
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("WIFI ERROR!");
    display.println("Connect to:");
    display.println(myWiFiManager->getConfigPortalSSID());
    display.println("192.168.4.1");
    display.display();
  #endif
}

// --- HTML DASHBOARD (Im Flash-Speicher) ---
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html><head><title>Climate Monitor</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;text-align:center;background:#121212;color:#eee;margin:0;padding-top:20px}
.c{background:#1e1e1e;padding:15px;margin:10px;width:140px;border-radius:12px;border-top:3px solid #777;display:inline-block}
.v{font-size:2rem;font-weight:bold}.u{font-size:1rem;color:#888}</style></head><body>
<h1>Room Climate</h1>
<div class="c" style="width:300px;border-top:5px solid #fff"><h2 style="margin:0;color:#aaa">Air Quality</h2><span id="q" style="font-size:1.5rem">...</span></div><br>
<div class="c" style="border-color:#ff5252"><span class="v" id="t">--</span><span class="u"> C</span></div>
<div class="c" style="border-color:#448aff"><span class="v" id="h">--</span><span class="u"> %</span></div>
<div class="c" style="border-color:#69f0ae"><span class="v" id="p">--</span><span class="u"> hPa</span></div>
<div class="c" style="border-color:#e040fb"><span class="v" id="g">--</span><span class="u"> kOhm</span></div>
<p id="devid" style="color:#555;font-size:0.8rem">Loading ID...</p>
<script>
setInterval(function(){fetch("/data").then(r=>r.json()).then(d=>{
document.getElementById("t").innerText=d.t.toFixed(1);
document.getElementById("h").innerText=d.h.toFixed(1);
document.getElementById("p").innerText=d.p.toFixed(0);
document.getElementById("g").innerText=(d.g/1000).toFixed(1);
document.getElementById("devid").innerText="ID: " + d.id;
const q=document.getElementById("q");q.innerText=d.q;
if(d.q.includes("Top")||d.q.includes("Good")){q.style.color="#00e676"}
else if(d.q.includes("Fair")){q.style.color="#ffeb3b"}
else{q.style.color="#ff1744"}
})},2000);
</script></body></html>)rawliteral";


// ==========================================
//                 SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(1000); // Warten für Serial Monitor
  Serial.println("\n--- SYSTEM START ---");

  // --- 1. DISPLAY INIT ---
  #ifdef USE_DISPLAY
    Serial.println("Init Display...");
    pinMode(PIN_OLED_RST, OUTPUT);
    digitalWrite(PIN_OLED_RST, LOW); delay(50); digitalWrite(PIN_OLED_RST, HIGH);
    Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL); 
    if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
       display.clearDisplay(); display.setTextColor(WHITE);
    }
  #endif

  showText("Booting...", "Init Sensors");

  // --- 2. SENSOR INIT ---
  
  // A) BME680
  #ifdef USE_BME680
    Serial.println("Init BME680...");
    I2C_BME.begin(PIN_BME_SDA, PIN_BME_SCL); 
    if (!bme.begin(0x77) && !bme.begin(0x76)) {
       Serial.println("BME Error");
       showText("ERROR", "BME Missing");
    } else {
       // Config BME
       bme.setTemperatureOversampling(BME680_OS_8X);
       bme.setHumidityOversampling(BME680_OS_2X);
       bme.setPressureOversampling(BME680_OS_4X);
       bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
       bme.setGasHeater(320, 150);
    }
  #endif

  // B) DHT
  #ifdef SENSOR_TYPE_DHT
    Serial.println("Init DHT...");
    dht.begin();
    // Kurzer Test
    float testT = dht.readTemperature();
    if (isnan(testT)) Serial.println("DHT Error: Keine Werte");
    else Serial.println("DHT OK");
  #endif

  // --- 3. WIFI ---
  WiFiManager wm;
  wm.setAPCallback(configModeCallback);
  wm.setConfigPortalTimeout(180);
  
  showText("WiFi...", "Connecting");
  
  if(!wm.autoConnect("Climate-Setup", "password")) {
    showText("OFFLINE", "Mode Active");
  } else {
    String ip = WiFi.localIP().toString();
    showText("Online!", ip);
    configTime(GMT_OFFSET_SEC, DST_OFFSET_SEC, NTP_SERVER_1, NTP_SERVER_2);
  }

  // --- 4. OTA ---
  ArduinoOTA.setHostname(OTA_HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASS);
  ArduinoOTA.begin();

  // --- 5. SERVER ---
  if(WiFi.status() == WL_CONNECTED) {
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){ request->send_P(200, "text/html", index_html); });
    
    // JSON API für das Frontend
    server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request){
      String json = "{";
      json += "\"id\":\"" + WiFi.macAddress() + "\",";
      json += "\"t\":" + String(temp) + ",";
      json += "\"h\":" + String(hum) + ",";
      json += "\"p\":" + String(pres) + ","; // Ist 0 bei DHT
      json += "\"g\":" + String(gas) + ",";  // Ist 0 bei DHT
      json += "\"q\":\"" + airQualityStatus + "\"";
      json += "}";
      request->send(200, "application/json", json);
    });
    
    server.begin();
    Serial.println("Webserver gestartet");
  }
}


// ==========================================
//                 LOOP
// ==========================================
void loop() {
  ArduinoOTA.handle(); 

  unsigned long currentMillis = millis();

  // --- MESSEN ---
  if ((currentMillis - lastSensorTime) > UPDATE_INTERVAL) {
    
    // A) BME LOGIK
    #ifdef USE_BME680
      if (bme.performReading()) {
        temp = bme.temperature;
        hum = bme.humidity;
        pres = bme.pressure / 100.0;
        gas = bme.gas_resistance;
        airQualityStatus = getAirQuality(gas);
      }
    #endif

    // B) DHT LOGIK
    #ifdef SENSOR_TYPE_DHT
      float t_read = dht.readTemperature();
      float h_read = dht.readHumidity();
      if (!isnan(t_read) && !isnan(h_read)) {
        temp = t_read;
        hum = h_read;
        pres = 0; // Kein Drucksensor
        gas = 0;  // Kein Gassensor
        airQualityStatus = "N/A";
      }
    #endif

    // --- DISPLAY UPDATE (Nur wenn Display vorhanden) ---
    #ifdef USE_DISPLAY
        display.clearDisplay();
        
        // Header
        display.setCursor(0,0); 
        if(WiFi.status() == WL_CONNECTED) {
           display.print("Online"); 
           String timeStr = getFormattedTime();
           int16_t x1, y1; uint16_t w, h;
           display.getTextBounds(timeStr, 0, 0, &x1, &y1, &w, &h);
           display.setCursor(128 - w, 0); display.print(timeStr);
        } else {
           display.print("Offline");
        }
        display.drawLine(0, 9, 128, 9, WHITE);
        
        // Values
        display.setCursor(0,15); display.printf("T: %.1f C", temp);
        display.setCursor(0,25); display.printf("H: %.0f %%", hum);
        display.setCursor(0,35); display.printf("P: %.0f", pres);
        display.setCursor(0,50); display.println(airQualityStatus);
        
        // Box Right
        display.drawRect(70, 15, 58, 30, WHITE);
        display.setCursor(74, 23); 
        if(airQualityStatus.startsWith("Top")) display.print("TOP");
        else if(airQualityStatus.startsWith("Good")) display.print("GOOD");
        else if(airQualityStatus.startsWith("Fair")) display.print("FAIR");
        else display.print("BAD");
        
        display.display();
    #else
        // Debug Output für C3/Ohne Display
        Serial.printf("MESSUNG -> T:%.1f H:%.0f\n", temp, hum);
    #endif
    
    lastSensorTime = currentMillis;
  }

  // --- SENDEN ---
  if ((currentMillis - lastSendTime) > SEND_INTERVAL) {
    sendDataToServer();
    lastSendTime = currentMillis;
  }
}
