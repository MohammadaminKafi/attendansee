import os
import shutil
from typing import List, Dict, Tuple
import numpy as np
from deepface import DeepFace


class FaceAggregator:
    """Aggregate face crops across sessions using DeepFace embeddings.

    Simple strategy:
    - compute embedding for each crop
    - compare to existing aggregated embeddings using cosine distance
    - if close enough (threshold), treat as same person and copy into that person's folder
    - otherwise create a new person folder
    """

    def __init__(self, model_name: str = "Facenet", distance_metric: str = "cosine", threshold: float = 0.4):
        self.model_name = model_name
        self.distance_metric = distance_metric
        self.threshold = threshold
        self.known_embeddings: List[np.ndarray] = []
        self.known_paths: List[str] = []

    def embed(self, img_path: str) -> np.ndarray:
        rep = DeepFace.represent(img_path=img_path, model_name=self.model_name, enforce_detection=False)
        # DeepFace returns list or dict depending on version; normalize
        if isinstance(rep, list) and len(rep) > 0:
            rep = rep[0]
        if isinstance(rep, dict) and "embedding" in rep:
            emb = np.array(rep["embedding"]).astype(np.float32)
        elif isinstance(rep, (list, tuple)):
            emb = np.array(rep).astype(np.float32)
        else:
            emb = np.array(rep).astype(np.float32)
        return emb

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 1.0
        return 1.0 - (np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def find_best_match(self, emb: np.ndarray) -> Tuple[int, float]:
        best_idx, best_score = -1, float("inf")
        for i, known in enumerate(self.known_embeddings):
            score = self._cosine(emb, known)
            if score < best_score:
                best_score = score
                best_idx = i
        return best_idx, best_score

    def aggregate(self, crops: List[Tuple[str, str]], out_dir: str) -> Dict[str, str]:
        """Aggregate a list of (crop_path, session_name) into person folders under out_dir.

        Behavior:
        - For each crop compute embedding and find best match among known embeddings.
        - If match found within threshold, assign to that person index, otherwise create new person.
        - Copy crop into out_dir/person_{i+1}/session_name/<cropfile> so the same person has duplicates per-session.

        Returns mapping crop_path -> person_folder
        """
        os.makedirs(out_dir, exist_ok=True)
        mapping = {}
        for crop, session in crops:
            try:
                emb = self.embed(crop)
            except Exception:
                # skip if embedding fails
                continue
            idx, score = self.find_best_match(emb)
            if idx >= 0 and score <= self.threshold:
                person_idx = idx
            else:
                person_idx = len(self.known_embeddings)
                self.known_embeddings.append(emb)
            person_folder = os.path.join(out_dir, f"person_{person_idx + 1}")
            session_folder = os.path.join(person_folder, session)
            os.makedirs(session_folder, exist_ok=True)
            dst = os.path.join(session_folder, os.path.basename(crop))
            try:
                shutil.copyfile(crop, dst)
            except Exception:
                # ignore copy errors
                continue
            mapping[crop] = person_folder
        return mapping
