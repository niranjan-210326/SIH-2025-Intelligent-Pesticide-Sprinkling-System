# run_wheat_analysis.py (Corrected for 10-second wait and new model)

import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2
import os
import time

class WheatAnalyzer:
    """Loads and uses the trained model for wheat analysis."""
    # --- MODIFIED: Load the new, balanced model ---
    def __init__(self, model_path='models/best_wheat_model_balanced.h5', data_dir='data/wheat_split/train'):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at '{model_path}'. Please run training first.")
        
        print("Loading Wheat Analysis Model...")
        self.model = keras.models.load_model(model_path, compile=False)
        self.class_names = sorted(os.listdir(data_dir))
        print(f"Model loaded. Classes: {self.class_names}")

    def analyze_frame(self, frame):
        """Analyzes a single image frame (from the webcam) and returns the prediction."""
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_resized = cv2.resize(image_rgb, (299, 299))
        image_normalized = image_resized.astype('float32') / 255.0
        image_expanded = np.expand_dims(image_normalized, axis=0)
        
        predictions = self.model.predict(image_expanded, verbose=0)
        
        confidence = float(np.max(predictions[0]))
        class_index = np.argmax(predictions[0])
        prediction_name = self.class_names[class_index]
        
        return {'prediction': prediction_name, 'confidence': confidence}

class PesticideRuleEngine:
    """Calculates pesticide dosage based on the analysis."""
    def __init__(self):
        self.PEST_CLASSES = ['Aphid', 'Mite', 'Stem fly']
        self.rules = { 'min_confidence': 0.80, 'dosage': { 'base_ml_per_1000sqm': 400, 'disease_multiplier': 1.5, 'pest_multiplier': 2.0, 'max_ml_per_1000sqm': 2500 } }

    def calculate_dosage(self, analysis_result, field_area_sqm=1000):
        # This function is unchanged
        prediction = analysis_result['prediction']
        confidence = analysis_result['confidence']
        if confidence < self.rules['min_confidence']:
            return {'spray_recommended': False, 'reason': f'Confidence ({confidence:.1%}) is below threshold.', 'amount_ml': 0}
        if prediction == 'Healthy':
            return {'spray_recommended': False, 'reason': 'Plant is healthy.', 'amount_ml': 0}
        is_pest = prediction in self.PEST_CLASSES
        base_amount = self.rules['dosage']['base_ml_per_1000sqm']
        multiplier = self.rules['dosage']['pest_multiplier'] if is_pest else self.rules['dosage']['disease_multiplier']
        calculated_amount = base_amount * multiplier
        scaled_dosage = (calculated_amount / 1000) * field_area_sqm
        max_dosage = (self.rules['dosage']['max_ml_per_1000sqm'] / 1000) * field_area_sqm
        final_amount = min(scaled_dosage, max_dosage)
        issue_type = "Pest" if is_pest else "Disease"
        reason = f"{issue_type} Detected: {prediction} (Confidence: {confidence:.1%})"
        return { 'spray_recommended': True, 'reason': reason, 'amount_ml': round(final_amount, 2) }

def run_live_analysis():
    """Initializes the system and runs the analysis in a continuous loop using the webcam."""
    try:
        analyzer = WheatAnalyzer()
        rule_engine = PesticideRuleEngine()
    except FileNotFoundError as e:
        print(f"FATAL ERROR: {e}")
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("FATAL ERROR: Could not open webcam.")
        return

    print("\n--- Starting Live Analysis Loop ---")
    print("Press Ctrl+C in this terminal to stop the program.")

    try:
        while True:
            print("\nCapturing image...")
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame from webcam. Exiting.")
                break
            
            analysis_result = analyzer.analyze_frame(frame)
            recommendation = rule_engine.calculate_dosage(analysis_result)

            print("\n--- WHEAT ANALYSIS REPORT ---")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Identified Issue: {analysis_result['prediction']}")
            print(f"Model Confidence: {analysis_result['confidence']:.2%}")
            print("-" * 30)
            print(f"Spray Recommended: {'YES' if recommendation['spray_recommended'] else 'NO'}")
            if recommendation['spray_recommended']:
                print(f"Calculated Dosage (1000 sqm): {recommendation['amount_ml']} ml")
            print(f"Reason: {recommendation['reason']}")
            print("--- END OF REPORT ---")
            
            # --- MODIFIED: Increased wait time ---
            print("\nWaiting for 10 seconds... Move the camera to the next location.")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\nCtrl+C detected. Shutting down the program.")
    finally:
        cap.release()
        print("Webcam released.")

if __name__ == "__main__":
    run_live_analysis()