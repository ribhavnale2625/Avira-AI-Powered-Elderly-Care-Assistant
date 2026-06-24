#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>

// ================= WiFi Credentials =================
const char* WIFI_SSID     = "KyaKarogeJaanKe";
const char* WIFI_PASSWORD = "12345678";

// ================= Backend Configuration =================
// Change this to the IP address of your server running server.py
const char* BACKEND_SERVER = "http://192.168.1.150:5000";

// ================= Hardcoded Pins =================
#define PIN_BUZZER         14  // Local warning active buzzer
#define PIN_LED            13  // Local status/warning LED
#define PIN_CANCEL_BTN     12  // Manual cancellation push-button (Active Low, INPUT_PULLUP)

// ================= MPU6050 Registers =================
#define MPU6050_ADDR       0x68
#define REG_PWR_MGMT_1     0x6B
#define REG_ACCEL_XOUT_H   0x3B

// ================= States Definition =================
enum SystemState {
  STATE_MONITORING,
  STATE_VERIFYING,
  STATE_WARNING,
  STATE_ALERTING,
  STATE_COOLOFF
};

SystemState currentState = STATE_MONITORING;

// ================= Offsets & Calibration =================
float offset_ax = 0;
float offset_ay = 0;
float offset_az = 0; // Gravitational acceleration offset
float offset_gx = 0;
float offset_gy = 0;
float offset_gz = 0;

// ================= Global Sync State =================
String ha_esp32_ip = "";
unsigned long lastRegisterTime = 0;
const unsigned long REGISTER_INTERVAL = 30000; // Re-register/sync every 30 seconds

// ================= Fall Detection Tuning Parameters =================
const float FREE_FALL_THRESHOLD   = 0.40;  // in g (magnitude drops below this during free fall)
const float IMPACT_THRESHOLD      = 2.50;  // in g (acceleration spike during impact)
const unsigned long IMPACT_WINDOW = 1000;  // ms (time window after free fall to detect impact)

// ================= Post-Fall Inactivity Parameters =================
const unsigned long VERIFY_WINDOW = 2000;  // ms (duration to monitor activity post-impact)
const float ACTIVITY_ACC_DELTA    = 0.35;  // in g (maximum acceleration difference allowed)
const float ACTIVITY_GYRO_LIMIT   = 40.0;  // in deg/s (maximum angular velocity allowed)

// ================= Warnings & Alerts =================
const unsigned long WARNING_DURATION = 5000; // 5 seconds warning window before dispatch

// ================= Control Variables =================
bool freeFallDetected = false;
unsigned long freeFallTime = 0;

// Variables for Verification Phase
unsigned long verificationStartTime = 0;
float maxAccVal = 0;
float minAccVal = 999;
float maxGyroVal = 0;

// Variables for Warning Phase
unsigned long warningStartTime = 0;
unsigned long lastWarningBeep = 0;
int warningBeepCount = 0;
bool warningLEDState = false;

// Variables for Cool-off Phase
unsigned long cooloffStartTime = 0;
const unsigned long COOLOFF_DURATION = 10000; // 10 seconds cool-off to prevent duplicate SOS

// ================= Buzzer Helpers =================
void playTone(int frequency, int durationMs) {
  // Simple square wave tone generator using digitalWrite
  // Since active buzzers beep when high, we can also use PWM or standard digitalWrite beeps
  // For active buzzers, we just toggle pin HIGH and LOW at the frequency period
  long delayUs = 1000000 / (frequency * 2);
  long numCycles = (frequency * durationMs) / 1000;
  for (long i = 0; i < numCycles; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(PIN_BUZZER, LOW);
    delayMicroseconds(delayUs);
  }
}

void playAscendingTone() {
  playTone(800, 100);
  delay(50);
  playTone(1200, 100);
  delay(50);
  playTone(1600, 150);
}

void playDescendingTone() {
  playTone(1600, 100);
  delay(50);
  playTone(1200, 100);
  delay(50);
  playTone(800, 150);
}

void playSuccessTone() {
  playTone(2000, 80);
  delay(40);
  playTone(2000, 80);
}

void playWarningTone() {
  playTone(1000, 150);
}

void playAlertTone() {
  playTone(3000, 2000);
}

// ================= MPU6050 direct read =================
bool readSensor(float &ax, float &ay, float &az, float &gx, float &gy, float &gz) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(REG_ACCEL_XOUT_H);
  if (Wire.endTransmission(false) != 0) {
    return false; // Connection error
  }
  
  Wire.requestFrom(MPU6050_ADDR, 14, true);
  if (Wire.available() < 14) {
    return false;
  }

  int16_t raw_ax = Wire.read() << 8 | Wire.read();
  int16_t raw_ay = Wire.read() << 8 | Wire.read();
  int16_t raw_az = Wire.read() << 8 | Wire.read();
  int16_t raw_temp = Wire.read() << 8 | Wire.read(); // temperature, skipped
  int16_t raw_gx = Wire.read() << 8 | Wire.read();
  int16_t raw_gy = Wire.read() << 8 | Wire.read();
  int16_t raw_gz = Wire.read() << 8 | Wire.read();

  // Convert raw accelerometer values to g (+/- 2g range -> 16384 LSB/g)
  ax = (raw_ax - offset_ax) / 16384.0;
  ay = (raw_ay - offset_ay) / 16384.0;
  // Account for gravity in calibration: z offset is calibrated flat, so raw_az - offset_az gives acceleration minus gravity.
  // We add gravity vector back to az to represent full magnitude relative to space.
  az = (raw_az - offset_az) / 16384.0;

  // Convert raw gyroscope values to deg/s (+/- 250 deg/s range -> 131 LSB / (deg/s))
  gx = (raw_gx - offset_gx) / 131.0;
  gy = (raw_gy - offset_gy) / 131.0;
  gz = (raw_gz - offset_gz) / 131.0;

  return true;
}

// ================= Sensor Calibration =================
void calibrateMPU6050() {
  Serial.println("⚙️ Calibrating MPU6050. Please keep the device completely flat and still...");
  digitalWrite(PIN_LED, HIGH);
  
  long sum_ax = 0, sum_ay = 0, sum_az = 0;
  long sum_gx = 0, sum_gy = 0, sum_gz = 0;
  const int numSamples = 200;

  for (int i = 0; i < numSamples; i++) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(REG_ACCEL_XOUT_H);
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_ADDR, 14, true);

    if (Wire.available() >= 14) {
      sum_ax += (Wire.read() << 8 | Wire.read());
      sum_ay += (Wire.read() << 8 | Wire.read());
      sum_az += (Wire.read() << 8 | Wire.read());
      Wire.read(); Wire.read(); // skip temp
      sum_gx += (Wire.read() << 8 | Wire.read());
      sum_gy += (Wire.read() << 8 | Wire.read());
      sum_gz += (Wire.read() << 8 | Wire.read());
    }
    delay(10);
  }

  offset_ax = sum_ax / (float)numSamples;
  offset_ay = sum_ay / (float)numSamples;
  // Z axis will feel gravity (+1g) when lying flat, so raw offset is calibration minus 1g LSB (16384)
  offset_az = (sum_az / (float)numSamples) - 16384.0;
  
  offset_gx = sum_gx / (float)numSamples;
  offset_gy = sum_gy / (float)numSamples;
  offset_gz = sum_gz / (float)numSamples;

  Serial.println("✅ Calibration Complete!");
  Serial.printf("Offsets -> Accel X: %.1f, Y: %.1f, Z: %.1f | Gyro X: %.1f, Y: %.1f, Z: %.1f\n", 
                offset_ax, offset_ay, offset_az, offset_gx, offset_gy, offset_gz);
  
  digitalWrite(PIN_LED, LOW);
  playSuccessTone();
}

// ================= Register with Backend =================
void registerWithBackend() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(BACKEND_SERVER) + "/api/esp32/register";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  JsonDocument doc;
  doc["role"] = "fall_detection";
  doc["ip"] = WiFi.localIP().toString();

  String payload;
  serializeJson(doc, payload);

  Serial.printf("[HTTP] Registering with backend: %s\n", url.c_str());
  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    Serial.printf("[HTTP] Registration Response Code: %d\n", httpResponseCode);
    
    if (httpResponseCode == 200) {
      String response = http.getString();
      Serial.println("[HTTP] Response: " + response);
      
      // Parse response to extract home_automation_ip
      JsonDocument responseDoc;
      DeserializationError error = deserializeJson(responseDoc, response);
      if (!error) {
        const char* ha_ip = responseDoc["home_automation_ip"];
        if (ha_ip != nullptr) {
          ha_esp32_ip = String(ha_ip);
          Serial.print("🔗 Synced Home Automation ESP32 IP: ");
          Serial.println(ha_esp32_ip);
        }
      }
    }
  } else {
    Serial.printf("[HTTP] Failed to register. Error: %d\n", httpResponseCode);
  }
  http.end();
}

// ================= Trigger SOS Alerts =================
void triggerFallAlert() {
  Serial.println("📢 SOS TRIGGER ACTIVATED! Sending alerts to backend & home automation ESP32...");

  // 1. Notify Backend
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(BACKEND_SERVER) + "/api/sos/trigger";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    JsonDocument doc;
    doc["trigger_type"] = "fall_detection";

    String payload;
    serializeJson(doc, payload);

    Serial.printf("[HTTP] Notifying backend at: %s\n", url.c_str());
    int httpResponseCode = http.POST(payload);
    Serial.printf("[HTTP] Backend response code: %d\n", httpResponseCode);
    http.end();
  }

  // 2. Notify Home Automation ESP32 Locally to trigger alarm/LCD
  if (WiFi.status() == WL_CONNECTED && ha_esp32_ip != "") {
    HTTPClient http;
    String url = "http://" + ha_esp32_ip + "/sos/trigger";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    Serial.printf("[HTTP] Triggering local HA alarm: %s\n", url.c_str());
    int httpResponseCode = http.POST("{}");
    Serial.printf("[HTTP] HA ESP32 response: %d\n", httpResponseCode);
    http.end();
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  
  // Set up local warning pins
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  
  pinMode(PIN_CANCEL_BTN, INPUT_PULLUP); // Push-button with internal pullup

  // Wake up MPU6050
  Wire.begin();
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(REG_PWR_MGMT_1);
  Wire.write(0); // wake up MPU-6050
  if (Wire.endTransmission(true) != 0) {
    Serial.println("❌ ERROR: MPU6050 not found! Please check I2C wiring.");
    while (1) {
      digitalWrite(PIN_LED, HIGH);
      delay(100);
      digitalWrite(PIN_LED, LOW);
      delay(100);
    }
  }
  Serial.println("🚀 MPU6050 Connected and Initialized.");
  
  // Play friendly startup sound
  playAscendingTone();
  
  // Calibrate baseline values
  calibrateMPU6050();

  // Connect to WiFi
  Serial.printf("Connecting to WiFi SSID: %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Register IP with backend
    registerWithBackend();
    lastRegisterTime = millis();
  } else {
    Serial.println("\n❌ WiFi Connection FAILED (Will operate in offline warning/local buzzer mode)");
  }
}

// ================= LOOP =================
void loop() {
  // Periodic sync of Home Automation IP
  if (WiFi.status() == WL_CONNECTED && (millis() - lastRegisterTime > REGISTER_INTERVAL)) {
    registerWithBackend();
    lastRegisterTime = millis();
  }

  float ax, ay, az;
  float gx, gy, gz;

  if (!readSensor(ax, ay, az, gx, gy, gz)) {
    Serial.println("⚠️ MPU6050 read failed!");
    delay(100);
    return;
  }

  // Calculate total acceleration magnitude
  float total_acc = sqrt(ax * ax + ay * ay + az * az);

  // Core State Machine
  switch (currentState) {
    
    case STATE_MONITORING: {
      // 1. Free fall: Acceleration drops significantly below 1g (< 0.40g)
      if (total_acc < FREE_FALL_THRESHOLD) {
        if (!freeFallDetected) {
          freeFallDetected = true;
          freeFallTime = millis();
          Serial.printf("⚠️ FREE FALL DETECTED! Accel: %.2f g\n", total_acc);
        }
      }

      // 2. Impact check: High acceleration spike (> 2.5g) within 1 second of free fall
      if (freeFallDetected) {
        if (millis() - freeFallTime > IMPACT_WINDOW) {
          freeFallDetected = false; // Reset if window expired
        } else if (total_acc > IMPACT_THRESHOLD) {
          Serial.printf("🚨 IMPACT DETECTED! Accel: %.2f g | Transitioning to Verification Phase...\n", total_acc);
          freeFallDetected = false;
          
          // Setup Verification Phase variables
          currentState = STATE_VERIFYING;
          verificationStartTime = millis();
          maxAccVal = total_acc;
          minAccVal = total_acc;
          maxGyroVal = 0;
        }
      }
      break;
    }

    case STATE_VERIFYING: {
      // Monitor inactivity / post-fall movement for 2 seconds
      if (total_acc > maxAccVal) maxAccVal = total_acc;
      if (total_acc < minAccVal) minAccVal = total_acc;
      
      // Gyro magnitude
      float gyro_mag = sqrt(gx * gx + gy * gy + gz * gz);
      if (gyro_mag > maxGyroVal) maxGyroVal = gyro_mag;

      // When verification window is up, check inactivity criteria
      if (millis() - verificationStartTime >= VERIFY_WINDOW) {
        float acc_delta = maxAccVal - minAccVal;
        
        Serial.printf("[Verify] Post-impact statistics: Accel Delta: %.2fg | Max Gyro Rate: %.1f deg/s\n", 
                      acc_delta, maxGyroVal);

        // If the user has high activity (moving to recover or sitting up), it's a false alarm
        if (acc_delta > ACTIVITY_ACC_DELTA || maxGyroVal > ACTIVITY_GYRO_LIMIT) {
          Serial.println("🔄 Inactivity check failed: Active movement detected post-impact. Alert cancelled.");
          currentState = STATE_MONITORING;
        } else {
          // No movement detected -> transition to user warning phase
          Serial.println("⚠️ User is inactive post-impact. Transitioning to Pre-Alert Warning Phase...");
          currentState = STATE_WARNING;
          warningStartTime = millis();
          lastWarningBeep = 0;
          warningBeepCount = 0;
        }
      }
      break;
    }

    case STATE_WARNING: {
      // Fast check for cancellation button (Active Low, pressed when LOW)
      if (digitalRead(PIN_CANCEL_BTN) == LOW) {
        Serial.println("❌ MANUAL CANCELLATION DETECTED! Aborting alarm...");
        digitalWrite(PIN_LED, LOW);
        digitalWrite(PIN_BUZZER, LOW);
        
        // Play happy cancellation tone
        playDescendingTone();
        delay(100);
        playSuccessTone();
        
        currentState = STATE_MONITORING;
        break;
      }

      // warning blink and beep logic
      unsigned long elapsed = millis() - warningStartTime;
      if (elapsed >= WARNING_DURATION) {
        // Warning expired, user did not cancel -> dispatch SOS
        Serial.println("🚨 Pre-alert warning expired without cancellation! Alerting Caregiver...");
        currentState = STATE_ALERTING;
      } else {
        // Toggle beeps and LEDs at 2Hz (every 500ms)
        if (millis() - lastWarningBeep >= 500) {
          lastWarningBeep = millis();
          warningLEDState = !warningLEDState;
          digitalWrite(PIN_LED, warningLEDState);
          
          if (warningLEDState) {
            playWarningTone();
            Serial.printf("🔔 [Warning Countdown] Press cancel button to abort! Time left: %d ms\n", 
                          (int)(WARNING_DURATION - elapsed));
          }
        }
      }
      break;
    }

    case STATE_ALERTING: {
      digitalWrite(PIN_LED, HIGH);
      
      // Dispatch alerts (locally to HA ESP32 & remotely to backend)
      triggerFallAlert();
      
      // Play loud siren beep to alert people nearby
      playAlertTone();
      
      digitalWrite(PIN_LED, LOW);
      currentState = STATE_COOLOFF;
      cooloffStartTime = millis();
      break;
    }

    case STATE_COOLOFF: {
      // 10 second cool-off period to prevent instant duplicate alerts while caregiver responds
      if (millis() - cooloffStartTime >= COOLOFF_DURATION) {
        Serial.println("🔄 Cool-off complete. Returning to Monitoring Mode...");
        currentState = STATE_MONITORING;
      }
      break;
    }
  }

  delay(10); // Standard loop stability delay
}
