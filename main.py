import os
import cv2
from deepface import DeepFace

# ---------- STEP 1: Define a function to draw rectangles around faces ----------

def draw_faces(img_path, output_path=None):
    img = cv2.imread(img_path)
    detections = DeepFace.extract_faces(img_path=img_path, detector_backend='retinaface', enforce_detection=False)
    for det in detections:
        area = det['facial_area']
        x, y, w, h = area['x'], area['y'], area['w'], area['h']
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    if output_path:
        cv2.imwrite(output_path, img)

# ---------- STEP 2: Run the function on all session images ----------

input_folder = "img/input/session2"
output_folder = "img/output/session2"
os.makedirs(output_folder, exist_ok=True)

for img_name in os.listdir(input_folder):
    if img_name.lower().endswith((".jpg", ".jpeg", ".png")):
        input_path = os.path.join(input_folder, img_name)
        output_path = os.path.join(output_folder, f"faces_{img_name}")
        print(f"Processing {img_name}...")
        draw_faces(input_path, output_path)

print("✅ Face detection completed. Results saved in 'output/session1'.")
