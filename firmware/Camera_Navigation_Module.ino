#include <WiFi.h>
#include <esp_camera.h>
#include <WebServer.h>
#include <HTTPClient.h>

// ====== CAMERA PINS (AI-Thinker Module) ======
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27

#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

// ====== MOTOR DRIVER PINS ======
#define IN1 14
#define IN2 15
#define IN3 13
#define IN4 12

// WiFi credentials
const char* ssid = "ZZZ";
const char* password = "12345";

// Web server
WebServer server(80);

// Server URL to send image
const char* serverURL = "http://192.168.18.235:5000/predict";

void setup() {
  Serial.begin(115200);

  // Setup motor pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  stopCar();

  // Camera config
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // Initialize camera
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: ");
  Serial.println(WiFi.localIP());

  // Setup web server routes
  server.on("/", handleRoot);
  server.on("/forward", [](){ forwardCar(); server.send(200, "text/html", "Forward"); });
  server.on("/backward", [](){ backwardCar(); server.send(200, "text/html", "Backward"); });
  server.on("/left", [](){ leftCar(); server.send(200, "text/html", "Left"); });
  server.on("/right", [](){ rightCar(); server.send(200, "text/html", "Right"); });
  server.on("/stop", [](){ stopCar(); server.send(200, "text/html", "Stop"); });
  server.on("/capture", [](){
    sendImageToServer();
    server.send(200, "text/plain", "Image sent!");
  });

  server.begin();
}

void loop() {
  server.handleClient();
}

// ====== Car Control Functions ======
void forwardCar() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void backwardCar() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void leftCar() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void rightCar() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void stopCar() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

// ====== Capture and Send Image ======
void sendImageToServer() {
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "image/jpeg");

    int httpResponseCode = http.POST(fb->buf, fb->len);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server response:");
      Serial.println(response);
    } else {
      Serial.print("Error sending image: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }

  esp_camera_fb_return(fb);
}

// ====== Web Page ======
void handleRoot() {
  String page = "<h1>ESP32-CAM Car Control</h1>";
  page += "<p><a href='/forward'>Forward</a></p>";
  page += "<p><a href='/backward'>Backward</a></p>";
  page += "<p><a href='/left'>Left</a></p>";
  page += "<p><a href='/right'>Right</a></p>";
  page += "<p><a href='/stop'>Stop</a></p>";
  page += "<hr>";
  page += "<p><a href='/capture'>Capture & Send Image</a></p>";
  server.send(200, "text/html", page);
}
