import os
import argparse
from typing import List

from face.extractor import FaceExtractor
from face.aggregator import FaceAggregator


def process_session(input_folder: str, output_folder: str, crops_subfolder: str = "crops") -> List[str]:
    os.makedirs(output_folder, exist_ok=True)
    extractor = FaceExtractor()
    saved_crops = []
    for img_name in sorted(os.listdir(input_folder)):
        if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        input_path = os.path.join(input_folder, img_name)
        annotated = os.path.join(output_folder, f"faces_{img_name}")
        crops_dir = os.path.join(output_folder, crops_subfolder, os.path.splitext(img_name)[0])
        print(f"Processing {input_path}...")
        try:
            saved = extractor.extract_and_save(input_path, annotated, crops_dir)
        except Exception as e:
            print(f"Failed to process {input_path}: {e}")
            continue
        for crop_path, meta in saved:
            saved_crops.append(crop_path)
    return saved_crops


def aggregate_sessions(session_crop_dirs: List[str], aggregate_out: str) -> None:
    aggregator = FaceAggregator()
    # Flatten list of crop paths
    all_crops = []
    for d in session_crop_dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                all_crops.append(os.path.join(d, f))
    if not all_crops:
        print("No crops found to aggregate.")
        return
    mapping = aggregator.aggregate(all_crops, aggregate_out)
    print(f"Aggregated {len(mapping)} crops into {aggregate_out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="img/input", help="Input root with session folders")
    parser.add_argument("--output", default="img/output", help="Output root for annotated images and crops")
    parser.add_argument("--aggregate", default="img/aggregated", help="Folder to store aggregated persons")
    args = parser.parse_args()

    input_root = args.input
    output_root = args.output
    aggregate_out = args.aggregate

    session_crop_dirs = []
    for name in sorted(os.listdir(input_root)):
        session_in = os.path.join(input_root, name)
        if not os.path.isdir(session_in):
            continue
        session_out = os.path.join(output_root, name)
        crops = process_session(session_in, session_out)
        # crops saved under session_out/crops/<imgname>/*.png
        session_crops_dir = os.path.join(session_out, "crops")
        session_crop_dirs.append((session_crops_dir, name))

    # Build list of (crop_path, session_name) pairs
    pairs = []
    for dirpath, session_name in session_crop_dirs:
        if not os.path.isdir(dirpath):
            continue
        for root, _, files in os.walk(dirpath):
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    pairs.append((os.path.join(root, f), session_name))

    if pairs:
        aggregator = FaceAggregator()
        mapping = aggregator.aggregate(pairs, aggregate_out)
        print(f"Aggregated {len(mapping)} crops into {aggregate_out}")
    else:
        print("No face crops found to aggregate across sessions.")


if __name__ == "__main__":
    main()
