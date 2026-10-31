#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ========================================
// DATA MODE CONFIGURATION
// ========================================

// true  = Generate dummy sensor data
// false = Read actual DS18B20 sensor data

#define USE_DUMMY_DATA false


// ========================================
// WIFI CONFIGURATION
// ========================================

const char* WIFI_SSID = "SSB";
const char* WIFI_PASSWORD = "12345678";


// ========================================
// SENSOR AND OLED PINS
// ========================================

#define DS18B20_PIN 27
#define OLED_SDA 21
#define OLED_SCL 20
#define OLED_ADDR 0x3C


// ========================================
// MATURITY CONFIGURATION
// ========================================

#define DATUM_TEMP_C -10.0
#define DEMO_MODE true

const float DEMO_MINUTES_PER_REAL_SECOND = 1.0;
const unsigned long SAMPLE_INTERVAL_MS = 10000;


// ========================================
// THINGSBOARD MQTT CONFIGURATION
// ========================================

const char* TB_SERVER = "mqtt.thingsboard.cloud";
const int TB_PORT = 1883;

const char* TB_TOKEN = "concrete";

const char* TB_TOPIC = "v1/devices/me/telemetry";


// ========================================
// WIFI AND MQTT CLIENTS
// ========================================

WiFiClient espClient;
PubSubClient mqttClient(espClient);


// ========================================
// SENSOR INITIALIZATION
// ========================================

OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);


// ========================================
// OLED INITIALIZATION
// ========================================

Adafruit_SSD1306 display(128, 64, &Wire, -1);


// ========================================
// MATURITY VARIABLES
// ========================================

float maturity_C_hour = 0.0;
float temperature_C = 0.0;
float simulated_hours = 0.0;

unsigned long lastSampleMs = 0;

unsigned long dummySampleCount = 0;


// ========================================
// WIFI CONNECTION
// ========================================

void connectWiFi() {

    if (WiFi.status() == WL_CONNECTED) {
        return;
    }

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to Wi-Fi");

    unsigned long start = millis();

    while (WiFi.status() != WL_CONNECTED &&
           millis() - start < 20000) {

        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {

        Serial.println("\nWi-Fi connected!");

        Serial.print("ESP32 IP: ");
        Serial.println(WiFi.localIP());

    } else {

        Serial.println("\nWi-Fi connection failed.");
    }
}


// ========================================
// THINGSBOARD MQTT CONNECTION
// ========================================

bool connectThingsBoard() {

    if (mqttClient.connected()) {
        return true;
    }

    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    if (WiFi.status() != WL_CONNECTED) {

        Serial.println("Cannot connect to ThingsBoard: No Wi-Fi");

        return false;
    }

    Serial.println("Connecting to ThingsBoard...");

    if (mqttClient.connect(
            "ESP32_Concrete_Maturity",
            TB_TOKEN,
            ""
        )) {

        Serial.println("ThingsBoard MQTT connected!");

        return true;

    } else {

        Serial.print("MQTT connection failed. State: ");
        Serial.println(mqttClient.state());

        return false;
    }
}


// ========================================
// GENERATE DUMMY DATA
// ========================================

void generateDummyData(float dt_hours) {

    // Generate changing temperature values:
    // 28.0, 28.5, 29.0, 29.5 ... 31.5
    // Then repeat the sequence.

    temperature_C = 28.0 +
        (dummySampleCount % 8) * 0.5;

    dummySampleCount++;

    // Update simulated curing time
    simulated_hours += dt_hours;

    // Calculate Nurse-Saul maturity
    float increment =
        (temperature_C - DATUM_TEMP_C) * dt_hours;

    if (increment > 0.0) {

        maturity_C_hour += increment;
    }

    Serial.println("DUMMY DATA GENERATED");

    Serial.print("Dummy temperature: ");
    Serial.println(temperature_C, 2);

    Serial.print("Dummy maturity: ");
    Serial.println(maturity_C_hour, 3);

    Serial.print("Dummy time: ");
    Serial.println(simulated_hours, 3);
}


// ========================================
// READ REAL SENSOR DATA
// ========================================

bool readRealSensor(float dt_hours) {

    sensors.requestTemperatures();

    temperature_C = sensors.getTempCByIndex(0);

    if (temperature_C == DEVICE_DISCONNECTED_C) {

        Serial.println("ERROR: DS18B20 disconnected");

        return false;
    }

    // Update simulated or real curing time
    simulated_hours += dt_hours;

    // Calculate Nurse-Saul maturity
    float increment =
        (temperature_C - DATUM_TEMP_C) * dt_hours;

    if (increment > 0.0) {

        maturity_C_hour += increment;
    }

    return true;
}


// ========================================
// OLED DISPLAY
// ========================================

void drawDisplay() {

    display.clearDisplay();

    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);

    display.setCursor(0, 0);
    display.println("CONCRETE MATURITY");

    display.setCursor(0, 14);
    display.print("Temp: ");
    display.print(temperature_C, 1);
    display.println(" C");

    display.setCursor(0, 26);
    display.print("Time: ");
    display.print(simulated_hours, 2);
    display.println(" h");

    display.setCursor(0, 38);
    display.println("Maturity:");

    display.setCursor(0, 50);
    display.print(maturity_C_hour, 1);
    display.println(" C.h");

    display.display();
}


// ========================================
// SEND DATA TO THINGSBOARD
// ========================================

void sendToThingsBoard() {

    if (!mqttClient.connected()) {

        if (!connectThingsBoard()) {

            Serial.println("Reading not sent to ThingsBoard.");

            return;
        }
    }

    // Prepare JSON telemetry
    String json = "{";

    json += "\"sensor_id\":1,";
    json += "\"temperature_c\":" + String(temperature_C, 2) + ",";
    json += "\"maturity_c_hour\":" + String(maturity_C_hour, 3) + ",";
    json += "\"simulated_hours\":" + String(simulated_hours, 3) + ",";
    json += "\"sensor_status\":true,";

    // Identify whether data is simulated or real
    json += "\"data_mode\":\"";
    json += USE_DUMMY_DATA ? "dummy" : "real";
    json += "\"";

    json += "}";

    Serial.println("Sending data to ThingsBoard:");
    Serial.println(json);

    // Publish MQTT telemetry
    bool success = mqttClient.publish(
        TB_TOPIC,
        json.c_str()
    );

    if (success) {

        Serial.println("ThingsBoard telemetry sent successfully!");

    } else {

        Serial.println("ThingsBoard telemetry sending failed!");
    }
}


// ========================================
// SETUP
// ========================================

void setup() {

    Serial.begin(115200);

    delay(500);

    // Initialize temperature sensor
    sensors.begin();

    // Initialize OLED
    Wire.begin(OLED_SDA, OLED_SCL);

    if (!display.begin(
            SSD1306_SWITCHCAPVCC,
            OLED_ADDR
        )) {

        Serial.println("OLED initialization failed!");

        while (true) {
            delay(100);
        }
    }

    drawDisplay();

    Serial.println("================================");
    Serial.println(" CONCRETE MATURITY METER");
    Serial.println(" ESP32 + ThingsBoard MQTT");
    Serial.println("================================");

    // Display selected data mode
    #if USE_DUMMY_DATA
        Serial.println("DATA MODE: DUMMY DATA");
    #else
        Serial.println("DATA MODE: REAL DS18B20");
    #endif

    Serial.println(
        "Time_hours,Temperature_C,Maturity_C_hour"
    );

    // Configure MQTT
    mqttClient.setServer(TB_SERVER, TB_PORT);
    mqttClient.setKeepAlive(30);
    mqttClient.setSocketTimeout(5);

    // Connect Wi-Fi
    connectWiFi();

    // Connect ThingsBoard
    if (WiFi.status() == WL_CONNECTED) {

        connectThingsBoard();
    }
}


// ========================================
// MAIN LOOP
// ========================================

void loop() {

    // Maintain MQTT connection
    if (WiFi.status() == WL_CONNECTED) {

        mqttClient.loop();
    }

    unsigned long now = millis();

    // Sample every 10 seconds
    if (now - lastSampleMs < SAMPLE_INTERVAL_MS) {

        return;
    }

    float dt_hours = 0.0;

    if (lastSampleMs != 0) {

        float real_dt_seconds =
            (now - lastSampleMs) / 1000.0;

        dt_hours = DEMO_MODE
            ? (real_dt_seconds *
               DEMO_MINUTES_PER_REAL_SECOND) / 60.0
            : real_dt_seconds / 3600.0;
    }

    lastSampleMs = now;


    // ====================================
    // SELECT DATA SOURCE
    // ====================================

    #if USE_DUMMY_DATA

        // Generate simulated sensor readings
        generateDummyData(dt_hours);

    #else

        // Read actual DS18B20 sensor
        if (!readRealSensor(dt_hours)) {

            return;
        }

    #endif


    // ====================================
    // UPDATE OLED
    // ====================================

    drawDisplay();


    // ====================================
    // PRINT SENSOR DATA
    // ====================================

    Serial.println("Sensor Readings:");

    Serial.print("Time: ");
    Serial.print(simulated_hours, 3);
    Serial.println(" hours");

    Serial.print("Temperature: ");
    Serial.print(temperature_C, 2);
    Serial.println(" C");

    Serial.print("Maturity: ");
    Serial.print(maturity_C_hour, 3);
    Serial.println(" C.h");


    // ====================================
    // SEND DATA TO THINGSBOARD
    // ====================================

    sendToThingsBoard();

    Serial.println("--------------------------------");
}