#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <HTTPClient.h>

// ================= WiFi =================
const char* WIFI_SSID     = "KyaKarogeJaanKe";
const char* WIFI_PASSWORD = "12345678";

// ================= Backend Server =================
// Change this to the IP address of your server running server.py
const char* BACKEND_SERVER = "http://192.168.1.150:5000";

// ================= Pins =================
#define PIN_LIGHT_LIVING   2
#define PIN_LIGHT_BEDROOM  4
#define PIN_FAN_LIVING     5
#define PIN_FAN_BEDROOM    18
#define PIN_TV             19
#define PIN_DOOR_SERVO     21
#define PIN_SOS_BUZZER     22
#define PIN_SOS_LED        23

// ================= State =================
struct DeviceState {
  bool state;
  int value;
};

DeviceState lightLiving  = { false, 0 };
DeviceState lightBedroom = { false, 0 };
DeviceState fanLiving    = { false, 0 };
DeviceState fanBedroom   = { false, 0 };
DeviceState tv           = { false, 0 };
DeviceState doorLock     = { true,  0 };

// ================= SOS =================
bool sosActive = false;
unsigned long lastBlink = 0;
bool sosToggle = false;

// ================= Objects =================
WebServer server(80);
Servo doorServo;

// ================= Backend Registration =================
void registerWithBackend() {
  HTTPClient http;
  String url = String(BACKEND_SERVER) + "/api/esp32/register";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  JsonDocument doc;
  doc["role"] = "home_automation";
  doc["ip"] = WiFi.localIP().toString();
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.print("Registering with backend at: ");
  Serial.println(url);
  int httpResponseCode = http.POST(payload);
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println(response);
  } else {
    Serial.print("Error code on sending POST: ");
    Serial.println(httpResponseCode);
  }
  http.end();
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);

  // GPIO — all start OFF
  pinMode(PIN_LIGHT_LIVING, OUTPUT);
  digitalWrite(PIN_LIGHT_LIVING, LOW);

  pinMode(PIN_LIGHT_BEDROOM, OUTPUT);
  digitalWrite(PIN_LIGHT_BEDROOM, LOW);

  pinMode(PIN_FAN_LIVING, OUTPUT);
  digitalWrite(PIN_FAN_LIVING, LOW);

  pinMode(PIN_FAN_BEDROOM, OUTPUT);
  digitalWrite(PIN_FAN_BEDROOM, LOW);

  pinMode(PIN_TV, OUTPUT);
  digitalWrite(PIN_TV, LOW);

  doorServo.attach(PIN_DOOR_SERVO);
  doorServo.write(0);

  pinMode(PIN_SOS_BUZZER, OUTPUT);
  digitalWrite(PIN_SOS_BUZZER, LOW);
  pinMode(PIN_SOS_LED, OUTPUT);
  digitalWrite(PIN_SOS_LED, LOW);


  // ================= WiFi =================
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    // Register IP with backend
    registerWithBackend();
  } else {
    Serial.println("\n❌ WiFi FAILED");
  }

  // ================= Routes =================
  server.on("/light/living", HTTP_POST, handleLightLiving);
  server.on("/light/bedroom", HTTP_POST, handleLightBedroom);
  server.on("/fan/living", HTTP_POST, handleFanLiving);
  server.on("/fan/bedroom", HTTP_POST, handleFanBedroom);
  server.on("/tv", HTTP_POST, handleTV);
  server.on("/door", HTTP_POST, handleDoor);
  server.on("/sos/trigger", HTTP_POST, handleSOS);
  server.on("/sos/cancel", HTTP_POST, handleSOSCancel);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/ping", HTTP_GET, handlePing);

  server.begin();
  Serial.println("🚀 Server started");
}

// ================= LOOP =================
void loop() {
  server.handleClient();

  // SOS blinking
  if (sosActive && millis() - lastBlink > 200) {
    lastBlink = millis();
    sosToggle = !sosToggle;

    digitalWrite(PIN_SOS_BUZZER, sosToggle);
    digitalWrite(PIN_SOS_LED, sosToggle);
  }
}

// ================= JSON Helper =================
bool parseJSON(JsonDocument &doc) {
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  if (err) {
    server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
    return false;
  }
  return true;
}

// ================= HANDLERS =================

void handleLightLiving() {
  JsonDocument doc;
  if (!parseJSON(doc)) return;

  lightLiving.state = doc["state"] | false;
  digitalWrite(PIN_LIGHT_LIVING, lightLiving.state);

  server.send(200, "application/json", "{\"light_living\":true}");
}

void handleLightBedroom() {
  JsonDocument doc;
  if (!parseJSON(doc)) return;

  lightBedroom.state = doc["state"] | false;
  digitalWrite(PIN_LIGHT_BEDROOM, lightBedroom.state);

  server.send(200, "application/json", "{\"light_bedroom\":true}");
}

void handleFanLiving() {
  JsonDocument doc;
  if (!parseJSON(doc)) return;

  fanLiving.state = doc["state"] | false;
  digitalWrite(PIN_FAN_LIVING, fanLiving.state);

  server.send(200, "application/json", "{\"fan_living\":true}");
}

void handleFanBedroom() {
  JsonDocument doc;
  if (!parseJSON(doc)) return;

  fanBedroom.state = doc["state"] | false;
  digitalWrite(PIN_FAN_BEDROOM, fanBedroom.state);

  server.send(200, "application/json", "{\"fan_bedroom\":true}");
}

void handleTV() {
  JsonDocument doc;
  if (!parseJSON(doc)) return;

  tv.state = doc["state"] | false;
  digitalWrite(PIN_TV, tv.state);

  server.send(200, "application/json", "{\"tv\":true}");
}

void handleDoor() {
  JsonDocument doc;
  if (!parseJSON(doc)) return;

  doorLock.state = doc["state"] | true;
  doorServo.write(doorLock.state ? 0 : 90);

  server.send(200, "application/json", "{\"door\":true}");
}

void handleSOS() {
  sosActive = true;
  server.send(200, "application/json", "{\"sos\":\"ON\"}");
}

void handleSOSCancel() {
  sosActive = false;
  digitalWrite(PIN_SOS_BUZZER, LOW);
  digitalWrite(PIN_SOS_LED, LOW);

  server.send(200, "application/json", "{\"sos\":\"OFF\"}");
}

void handlePing() {
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleStatus() {
  JsonDocument doc;

  doc["wifi"] = WiFi.status() == WL_CONNECTED;
  doc["ip"] = WiFi.localIP().toString();
  doc["sos"] = sosActive;

  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output);
}