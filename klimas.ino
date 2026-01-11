#include <WiFi.h>
// 1. Erst WiFiManager und HTTPClient
#include <HTTPClient.h> 
#include <WiFiManager.h> 

// 2. Dann AsyncTCP
#include <AsyncTCP.h>

// 3. Fix für WebServer Konflikt
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

// 4. Dann ESPAsyncWebServer
#include <ESPAsyncWebServer.h>

// 5. Rest
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_BME680.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESPmDNS.h>
#include <ArduinoOTA.h>
#include "time.h" // NEU: Zeit-Bibliothek

#include "config.h" 

// --- OBJEKTE ---
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, PIN_OLED_RST);
TwoWire I2C_BME = TwoWire(1);
Adafruit_BME680 bme(&I2C_BME);
AsyncWebServer server(80);

// Variablen
float temp = 0.0, hum = 0.0, pres = 0.0, gas = 0.0;
String airQualityStatus = "Init..."; 
unsigned long lastSensorTime = 0;
unsigned long lastSendTime = 0;

// --- CALLBACK WIFIMANAGER ---
void configModeCallback (WiFiManager *myWiFiManager) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("WLAN KONFIGURATION");
  display.println("SSID: Heltec-Klima-Setup");
  display.println("IP: 192.168.4.1");
  display.display();
}

// Luftqualität
String getAirQuality(float gasResistance) {
  if (gasResistance > GAS_LEVEL_GOOD) return "Top (Sehr Gut)";
  else if (gasResistance > GAS_LEVEL_OK) return "Gut (Normal)";
  else if (gasResistance > GAS_LEVEL_WARN) return "Bedenklich";
  else if (gasResistance > 0) return "WARNUNG (Schlecht)";
  return "Init...";
}

// Daten senden
void sendDataToServer() {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClient client;
    HTTPClient http;
    http.setTimeout(3000); 
    http.begin(client, SERVER_URL);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    String httpRequestData = "api_key=" + String(API_KEY) 
                           + "&temperature=" + String(temp)
                           + "&humidity=" + String(hum)
                           + "&pressure=" + String(pres)
                           + "&gas=" + String(gas);
    int code = http.POST(httpRequestData);
    if(code > 0) Serial.printf("HTTP: %d\n", code);
    http.end();
  }
}

// --- ZEIT HOLEN (NEU) ---
String getFormattedTime() {
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)){
    return "--:--";
  }
  char timeStringBuff[6]; // HH:MM + Nullbyte
  strftime(timeStringBuff, sizeof(timeStringBuff), "%H:%M", &timeinfo);
  return String(timeStringBuff);
}

// --- HTML (Gekürzt, dein Design bleibt) ---
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head><title>Heltec Klima</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:sans-serif;text-align:center;background:#121212;color:#eee;margin:0;padding-top:20px}
.card{background:#1e1e1e;padding:15px;margin:10px;width:140px;border-radius:12px;box-shadow:0 4px 10px rgba(0,0,0,0.4);border-top:3px solid #777}
.val{font-size:2.0rem;font-weight:bold}.unit{font-size:1rem;color:#888}
.status-card{width:300px;border-top:5px solid #fff}#qual{font-size:1.5rem;color:#fff}
</style>
</head><body><h1>Raumklima</h1>
<div style="display:flex;justify-content:center"><div class="card status-card" id="card-qual"><h2>Luft</h2><p><span id="qual">...</span></p></div></div>
<div style="display:flex;justify-content:center;flex-wrap:wrap">
<div class="card" style="border-top-color:#ff5252"><h2>Temp</h2><p><span class="val" id="temp">--</span><span class="unit"> C</span></p></div>
<div class="card" style="border-top-color:#448aff"><h2>Hum</h2><p><span class="val" id="hum">--</span><span class="unit"> %</span></p></div>
<div class="card" style="border-top-color:#69f0ae"><h2>Pres</h2><p><span class="val" id="pres">--</span><span class="unit"> hPa</span></p></div>
<div class="card" style="border-top-color:#e040fb"><h2>Gas</h2><p><span class="val" id="gas">--</span><span class="unit"> kOhm</span></p></div>
</div>
<script>
setInterval(function(){fetch("/data").then(r=>r.json()).then(d=>{
document.getElementById("temp").innerText=d.t.toFixed(1);document.getElementById("hum").innerText=d.h.toFixed(1);
document.getElementById("pres").innerText=d.p.toFixed(0);document.getElementById("gas").innerText=(d.g/1000).toFixed(1);
const q=document.getElementById("qual"),c=document.getElementById("card-qual");q.innerText=d.q;
if(d.q.includes("Top")||d.q.includes("Gut")){c.style.borderTopColor="#00e676";q.style.color="#00e676"}
else if(d.q.includes("Bed")){c.style.borderTopColor="#ffeb3b";q.style.color="#ffeb3b"}
else{c.style.borderTopColor="#ff1744";q.style.color="#ff1744"}
})},2000);</script></body></html>)rawliteral";

void setup() {
  Serial.begin(115200);
  delay(500);

  // Hardware Init
  pinMode(PIN_OLED_RST, OUTPUT);
  digitalWrite(PIN_OLED_RST, LOW); delay(50); digitalWrite(PIN_OLED_RST, HIGH);
  Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL); 
  I2C_BME.begin(PIN_BME_SDA, PIN_BME_SCL); 

  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0,10); display.println("Booting..."); display.display();

  if (!bme.begin(0x77)) { if (!bme.begin(0x76)) { Serial.println("BME Fehler"); } }
  if (bme.temperature > 0) {
      bme.setTemperatureOversampling(BME680_OS_8X);
      bme.setHumidityOversampling(BME680_OS_2X);
      bme.setPressureOversampling(BME680_OS_4X);
      bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
      bme.setGasHeater(320, 150);
  }

  // WiFiManager
  WiFiManager wm;
  wm.setAPCallback(configModeCallback);
  wm.setConfigPortalTimeout(180); 
  
  if(!wm.autoConnect("Heltec-Klima-Setup", "password")) {
    display.println("Offline Modus"); display.display(); delay(1000);
  } else {
    display.clearDisplay(); display.setCursor(0,0);
    display.println("Online! IP:"); display.println(WiFi.localIP());
    display.display();
    
    // --- ZEIT SYNCHRONISIEREN (NEU) ---
    // Konfiguriere NTP (Server 1 und 2)
    configTime(GMT_OFFSET_SEC, DST_OFFSET_SEC, NTP_SERVER_1, NTP_SERVER_2);
  }

  // OTA
  ArduinoOTA.setHostname(OTA_HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASS);
  ArduinoOTA.begin();

  // Webserver
  if(WiFi.status() == WL_CONNECTED) {
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){ request->send_P(200, "text/html", index_html); });
    server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request){
      String json = "{";
      json += "\"t\":" + String(temp) + ",";
      json += "\"h\":" + String(hum) + ",";
      json += "\"p\":" + String(pres) + ",";
      json += "\"g\":" + String(gas) + ",";
      json += "\"q\":\"" + airQualityStatus + "\"";
      json += "}";
      request->send(200, "application/json", json);
    });
    server.begin();
  }
}

void loop() {
  ArduinoOTA.handle(); 

  unsigned long currentMillis = millis();

  if ((currentMillis - lastSensorTime) > UPDATE_INTERVAL) {
    if (bme.performReading()) {
      temp = bme.temperature;
      hum = bme.humidity;
      pres = bme.pressure / 100.0;
      gas = bme.gas_resistance;
      airQualityStatus = getAirQuality(gas);

      display.clearDisplay();
      
      // Kopfzeile: Links IP (oder Offline), Rechts UHRZEIT
      display.setCursor(0,0); 
      if(WiFi.status() == WL_CONNECTED) {
         // IP kurz anzeigen (letzter Block) oder Text "WLAN"
         // Platz ist eng, wir zeigen "Online"
         display.print("Online"); 
         
         // UHRZEIT RECHTS
         String timeStr = getFormattedTime();
         int16_t x1, y1; uint16_t w, h;
         display.getTextBounds(timeStr, 0, 0, &x1, &y1, &w, &h);
         display.setCursor(128 - w, 0); // Rechtsbündig
         display.print(timeStr);
      } else {
         display.print("Offline");
      }
      
      display.drawLine(0, 9, 128, 9, WHITE);
      display.setCursor(0,15); display.printf("T: %.1f C", temp);
      display.setCursor(0,25); display.printf("H: %.0f %%", hum);
      display.setCursor(0,35); display.printf("P: %.0f", pres);

      display.setCursor(0,50); display.println(airQualityStatus);
      
      // Rechte Box (Status)
      display.drawRect(70, 15, 58, 30, WHITE);
      display.setCursor(74, 23); 
      if(airQualityStatus.startsWith("Top")) display.print("TOP");
      else if(airQualityStatus.startsWith("Gut")) display.print("GUT");
      else if(airQualityStatus.startsWith("Bed")) display.print("NAJA");
      else display.print("BAD");
      
      display.display();
    }
    lastSensorTime = currentMillis;
  }

  if ((currentMillis - lastSendTime) > SEND_INTERVAL) {
    sendDataToServer();
    lastSendTime = currentMillis;
  }
}
