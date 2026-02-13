# train_wheat_system.py (Complete code with Offline Augmentation for Class Balancing)

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, save_img
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import matplotlib.pyplot as plt
import os
import numpy as np
import random

# --- 1. CONFIGURATION ---
BASE_PATH = 'data/wheat_split'
TRAIN_DIR = os.path.join(BASE_PATH, 'train')
VAL_DIR = os.path.join(BASE_PATH, 'val')
MODEL_SAVE_PATH = 'models/best_wheat_model_balanced.h5' # New model name
PLOT_SAVE_PATH = 'training_history_wheat_balanced.png'

# --- NEW: Set a target for the minimum number of images per class ---
TARGET_IMAGES_PER_CLASS = 600 # You can adjust this number

IMG_SIZE = (299, 299)
BATCH_SIZE = 32
INITIAL_EPOCHS = 15
FINETUNE_EPOCHS = 25
TOTAL_EPOCHS = INITIAL_EPOCHS + FINETUNE_EPOCHS

# --- 2. NEW: OFFLINE DATA AUGMENTATION FOR CLASS IMBALANCE ---
print("--- Starting Offline Data Augmentation to Balance Dataset ---")

augmentation_generator = ImageDataGenerator(
    rotation_range=40, width_shift_range=0.2, height_shift_range=0.2,
    shear_range=0.2, zoom_range=0.2, horizontal_flip=True,
    brightness_range=[0.8, 1.2], fill_mode='nearest'
)

class_dirs = [d for d in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, d))]

for class_name in class_dirs:
    class_path = os.path.join(TRAIN_DIR, class_name)
    # Ensure we only count image files, not other files
    image_files = [f for f in os.listdir(class_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    num_images = len(image_files)
    
    print(f"Class '{class_name}': Found {num_images} images.")
    
    if num_images > 0 and num_images < TARGET_IMAGES_PER_CLASS:
        num_to_generate = TARGET_IMAGES_PER_CLASS - num_images
        print(f"  -> Augmenting with {num_to_generate} new images...")
        
        original_images = [os.path.join(class_path, f) for f in image_files]
        
        for i in range(num_to_generate):
            random_image_path = random.choice(original_images)
            img = load_img(random_image_path)
            x = img_to_array(img)
            x = x.reshape((1,) + x.shape)
            
            for batch in augmentation_generator.flow(x, batch_size=1, 
                                                     save_to_dir=class_path, 
                                                     save_prefix=f'aug_{class_name}', 
                                                     save_format='jpg'):
                break # Generate one image per loop
print("--- Offline augmentation complete! ---\n")


# --- 3. DATA PREPARATION & ON-THE-FLY AUGMENTATION ---
print("--- Preparing Data Generators for Training ---")
train_datagen = ImageDataGenerator(
    rescale=1./255, rotation_range=40, width_shift_range=0.2,
    height_shift_range=0.2, shear_range=0.2, zoom_range=0.2,
    horizontal_flip=True, fill_mode='nearest'
)
validation_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    TRAIN_DIR, target_size=IMG_SIZE,
    batch_size=BATCH_SIZE, class_mode='categorical'
)
validation_generator = validation_datagen.flow_from_directory(
    VAL_DIR, target_size=IMG_SIZE,
    batch_size=BATCH_SIZE, class_mode='categorical'
)
NUM_CLASSES = len(train_generator.class_indices)
print(f"Found {NUM_CLASSES} classes: {list(train_generator.class_indices.keys())}")


# --- 4. MODEL BUILDING ---
print("\n--- Building Model using Transfer Learning (InceptionV3) ---")
base_model = InceptionV3(input_shape=(299, 299, 3), include_top=False, weights='imagenet')
base_model.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(1024, activation='relu')(x)
x = Dropout(0.5)(x)
predictions = Dense(NUM_CLASSES, activation='softmax')(x)
model = Model(inputs=base_model.input, outputs=predictions)

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# --- 5. STAGE 1: FEATURE EXTRACTION TRAINING ---
model_checkpoint = ModelCheckpoint(filepath=MODEL_SAVE_PATH, monitor='val_accuracy', save_best_only=True)
early_stopping = EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1)
early_stopping_ft = EarlyStopping(monitor='val_accuracy', patience=7, restore_best_weights=True, verbose=1)

print("\n--- Starting STAGE 1: Training the Top Layers ---")
history = model.fit(
    train_generator,
    epochs=INITIAL_EPOCHS,
    validation_data=validation_generator,
    callbacks=[early_stopping, model_checkpoint]
)

# --- 6. STAGE 2: FINE-TUNING ---
print("\n--- Starting STAGE 2: Fine-Tuning More Layers ---")
base_model.trainable = True
fine_tune_at_layer = 'mixed5'
fine_tune_at_index = [i for i, layer in enumerate(base_model.layers) if layer.name == fine_tune_at_layer][0]
for layer in base_model.layers[:fine_tune_at_index]:
    layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

history_fine = model.fit(
    train_generator,
    epochs=TOTAL_EPOCHS,
    initial_epoch=history.epoch[-1],
    validation_data=validation_generator,
    callbacks=[early_stopping_ft, model_checkpoint]
)

print(f"\n--- Training Complete! Best model saved to '{MODEL_SAVE_PATH}' ---")

# --- 7. VISUALIZE TRAINING RESULTS ---
acc = history.history.get('accuracy', []) + history_fine.history.get('accuracy', [])
val_acc = history.history.get('val_accuracy', []) + history_fine.history.get('val_accuracy', [])
loss = history.history.get('loss', []) + history_fine.history.get('loss', [])
val_loss = history.history.get('val_loss', []) + history_fine.history.get('val_loss', [])

epochs_range = range(len(acc))

plt.figure(figsize=(14, 6))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.axvline(x=len(history.history.get('accuracy', [])) - 1, color='r', linestyle='--', label='Start Fine-Tuning')
plt.legend(loc='lower right')
plt.title('Combined Training and Validation Accuracy')

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.axvline(x=len(history.history.get('loss', [])) - 1, color='r', linestyle='--', label='Start Fine-Tuning')
plt.legend(loc='upper right')
plt.title('Combined Training and Validation Loss')

plt.savefig(PLOT_SAVE_PATH)
print(f"Training history plot saved to '{PLOT_SAVE_PATH}'")

try:
    plt.show()
except Exception as e:
    print(f"Could not display plot interactively: {e}")
    print(f"Please view the saved image '{PLOT_SAVE_PATH}' instead.")
