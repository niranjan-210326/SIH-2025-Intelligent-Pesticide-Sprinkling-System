# Intelligent Pesticide Sprinkling System (SIH 2025)

**Problem Statement:** Intelligent Pesticide Sprinkling System Determined by the Infection Level of a Plant (ID: 25015)  
**Theme:** Agriculture, Food Tech & Rural Development  
**Team Name:** Eternal Minds

---

## 📌 Project Overview
This system is an AI-powered solution for precision agriculture. It uses a rail-mounted camera system to scan wheat and rice crops. Using the **GoogLeNet InceptionV3** architecture, it detects diseases and pests in real-time and triggers a localized sprayer only on the infected areas, reducing pesticide usage by up to 40%.

## 🧠 Software Logic
### 1. Training (train_wheat_system.py)
- Uses **Transfer Learning** with InceptionV3.
- Features **Offline Data Augmentation** to balance the dataset (ensuring the model learns rare diseases as well as common ones).
- Saves the trained "brain" as `best_wheat_model_balanced.h5`.

### 2. Live Analysis (run_wheat_analysis.py)
- Captures frames from the system camera.
- Uses a **Rule Engine** to calculate pesticide dosage based on the severity and type of infection detected.
- Communicates with hardware via Bluetooth to trigger the pump.

## 🛠️ Hardware Stack
- **Controllers:** Arduino Uno, ESP32-CAM, Raspberry Pi 5.
- **Sensors:** BME280 (Environment), Soil Moisture, Ultrasonic (Liquid Level).
- **Actuators:** DC Pesticide Pump, L298N Motor Driver (for rail movement).
- **Power:** Solar Panel + MPPT Charge Controller.

## 📁 Repository Structure
- `firmware/`: Contains Arduino and ESP32 code for hardware control.
- `train_wheat_system.py`: Script to train the AI model.
- `run_wheat_analysis.py`: Main script for live detection and pump control.
- `assets/`: Project diagrams and prototype photos.

---

## 👥 Credits
This project was a collaborative team effort. Original repository by [NimeVR](https://github.com/NimeVR). 

**Team members:** [Nime VR], [Keerthika S], [Nidharshanaa M], [Niranjan M P], [Subbaiah C], [Steve Johnson Rathinam G].
