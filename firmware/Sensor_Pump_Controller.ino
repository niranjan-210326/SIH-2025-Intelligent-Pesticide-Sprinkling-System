// Define Bluetooth module pins
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <SoftwareSerial.h>

// Define pins
const int soilMoisturePin = A0;
const int trigPin = 2;
const int echoPin = 3;
const int pumpPin = 5;
const int buttonPin = 4;

SoftwareSerial bluetoothSerial(10, 11); // RX, TX

// Define BME280 object
Adafruit_BME280 bme;

bool pumpState = false;

void setup() {
  Serial.begin(9600);
  bluetoothSerial.begin(9600);

  // Initialize BME280
  Wire.begin();
  bme.begin(0x76);

  // Initialize ultrasonic sensor
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Initialize pump and button
  pinMode(pumpPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
}

void loop() {
  // Read soil moisture level
  int soilMoistureLevel = analogRead(soilMoisturePin);
  Serial.print("Soil Moisture Level: ");
  Serial.println(soilMoistureLevel);
  bluetoothSerial.print("Soil Moisture Level: ");
  bluetoothSerial.println(soilMoistureLevel);

  // Read ultrasonic sensor distance
  long duration = ultrasonicRead(trigPin, echoPin);
  int distance = duration * 0.034 / 2;
  Serial.print("Liquid Level: ");
  Serial.print(distance);
  Serial.println(" cm");
  bluetoothSerial.print("Liquid Level: ");
  bluetoothSerial.print(distance);
  bluetoothSerial.println(" cm");

  // Read BME280 data
  float temperature = bme.readTemperature();
  float humidity = bme.readHumidity();
  float pressure = bme.readPressure() / 100.0F;
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" *C");
  bluetoothSerial.print("Temperature: ");
  bluetoothSerial.print(temperature);
  bluetoothSerial.println(" *C");
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");
  bluetoothSerial.print("Humidity: ");
  bluetoothSerial.print(humidity);
  bluetoothSerial.println(" %");
  Serial.print("Pressure: ");
  Serial.print(pressure);
  Serial.println(" hPa");
  bluetoothSerial.print("Pressure: ");
  bluetoothSerial.print(pressure);
  bluetoothSerial.println(" hPa");

  // Read button state
  if (digitalRead(buttonPin) == LOW) {
    pumpState = true;
    digitalWrite(pumpPin, HIGH);
    delay(10000);
    digitalWrite(pumpPin, LOW);
    pumpState = false;
  }

  // Handle Bluetooth commands
  if (bluetoothSerial.available() > 0) {
    String command = bluetoothSerial.readStringUntil('\n');
    if (command == "PUMP_ON") {
      pumpState = true;
      digitalWrite(pumpPin, HIGH);
      delay(10000);
      digitalWrite(pumpPin, LOW);
      pumpState = false;
    }
  }

  delay(1000);
}
