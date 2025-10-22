import os
from typing import List, Dict, Tuple
import cv2
from deepface import DeepFace


class FaceExtractor:
    """Utility to detect faces, draw rectangles, save face crops and metadata.

    Responsibilities:
    - detect faces in an image and draw rectangles on a copy
    - save the full image with rectangles to a path
    - save individual face crops to a directory and return metadata
    """

    def __init__(self, detector_backend: str = "retinaface"):
        self.detector_backend = detector_backend

    def detect(self, img_path: str) -> List[Dict]:
        """Run deepface extract_faces and return list of detections.

        Each detection is the raw dict returned by DeepFace.extract_faces.
        """
        detections = DeepFace.extract_faces(img_path=img_path, detector_backend=self.detector_backend, enforce_detection=False)
        return detections

    def draw_and_save(self, img_path: str, out_path: str, detections: List[Dict]) -> None:
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Image not found: {img_path}")
        for det in detections:
            area = det.get("facial_area")
            if not area:
                continue
            x, y, w, h = area["x"], area["y"], area["w"], area["h"]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cv2.imwrite(out_path, img)

    def save_crops(self, img_path: str, crops_dir: str, detections: List[Dict]) -> List[Tuple[str, Dict]]:
        """Save individual face crops into `crops_dir`.

        Returns list of tuples (crop_path, metadata) for each saved face.
        Metadata includes facial_area and source image.
        """
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Image not found: {img_path}")
        os.makedirs(crops_dir, exist_ok=True)
        saved = []
        base = os.path.splitext(os.path.basename(img_path))[0]
        for i, det in enumerate(detections):
            area = det.get("facial_area")
            if not area:
                continue
            x, y, w, h = area["x"], area["y"], area["w"], area["h"]
            # ensure within bounds
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(img.shape[1], x + w), min(img.shape[0], y + h)
            crop = img[y1:y2, x1:x2]
            crop_name = f"{base}_face{i + 1}.png"
            crop_path = os.path.join(crops_dir, crop_name)
            cv2.imwrite(crop_path, crop)
            meta = {"source": img_path, "facial_area": area, "crop_index": i}
            saved.append((crop_path, meta))
        return saved

    def extract_and_save(self, img_path: str, output_image_path: str, crops_dir: str) -> List[Tuple[str, Dict]]:
        detections = self.detect(img_path)
        # Draw rectangles and save annotated image
        self.draw_and_save(img_path, output_image_path, detections)
        # Save crops
        saved = self.save_crops(img_path, crops_dir, detections)
        return saved
