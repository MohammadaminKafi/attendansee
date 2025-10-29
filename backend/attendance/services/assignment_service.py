"""
Assignment service for matching face crops to students using embedding similarity.

Features:
- KNN over FaceCrop embeddings within the same class
- Cosine similarity using pgvector (fallback to numpy if needed)
- Two modes: auto-assign and suggestions-only
"""
from typing import List, Dict, Optional, Tuple

from django.db.models import QuerySet
from pgvector.django import CosineDistance
import numpy as np

from attendance.models import FaceCrop, Student


class AssignmentService:
	"""
	Service that provides utilities to find similar face crops and assign students.
	"""

	@staticmethod
	def _vector_to_list(vec) -> Optional[List[float]]:
		if vec is None:
			return None
		# pgvector returns list-like already; ensure list of floats
		return [float(x) for x in vec]

	@staticmethod
	def _cosine_similarity(a: List[float], b: List[float]) -> float:
		a_arr = np.asarray(a, dtype=np.float32)
		b_arr = np.asarray(b, dtype=np.float32)
		denom = (np.linalg.norm(a_arr) * np.linalg.norm(b_arr))
		if denom == 0:
			return 0.0
		return float(np.dot(a_arr, b_arr) / denom)

	@staticmethod
	def find_similar_crops(
		crop: FaceCrop,
		k: int = 5,
		embedding_model: Optional[str] = None,
		include_unidentified: bool = True,
	) -> List[Dict]:
		"""
		Find top-k similar face crops to the given crop within the same class.

		Returns a list of dicts with: crop_id, similarity, distance, student_id,
		student_name, crop_image_path, is_identified
		"""
		if crop.embedding is None:
			return []

		# Limit search to same class
		class_id = crop.image.session.class_session_id

		qs: QuerySet[FaceCrop] = FaceCrop.objects.filter(
			image__session__class_session_id=class_id,
			embedding__isnull=False,
		).exclude(id=crop.id)

		# Filter by embedding model if provided, otherwise use crop's model
		model_name = embedding_model or crop.embedding_model
		if model_name:
			qs = qs.filter(embedding_model=model_name)

		# If excluding unidentified, restrict to those linked to a student
		if not include_unidentified:
			qs = qs.filter(student__isnull=False)

		# Use pgvector cosine distance for ordering
		# distance in [0, 2], similarity = 1 - distance (when vectors are normalized)
		try:
			qs = qs.annotate(distance=CosineDistance('embedding', crop.embedding)).order_by('distance')
			neighbors = list(qs[:k])
			results: List[Dict] = []
			for n in neighbors:
				dist = getattr(n, 'distance', None)
				# Convert to similarity; clamp to [0,1]
				sim = 1.0 - float(dist) if dist is not None else AssignmentService._cosine_similarity(
					AssignmentService._vector_to_list(crop.embedding) or [],
					AssignmentService._vector_to_list(n.embedding) or [],
				)
				sim = max(0.0, min(1.0, sim))
				results.append({
					'crop_id': n.id,
					'student_id': n.student_id,
					'student_name': n.student.full_name if n.student_id else None,
					'similarity': sim,
					'distance': float(dist) if dist is not None else None,
					'crop_image_path': str(n.crop_image_path) if n.crop_image_path else '',
					'is_identified': bool(n.student_id is not None),
				})
			return results
		except Exception:
			# Fallback: fetch candidates and compute similarity in Python
			candidates = list(qs.values('id', 'student_id', 'crop_image_path', 'embedding'))
			query_emb = AssignmentService._vector_to_list(crop.embedding) or []
			for c in candidates:
				c['similarity'] = AssignmentService._cosine_similarity(query_emb, AssignmentService._vector_to_list(c['embedding']) or [])
			candidates.sort(key=lambda x: x['similarity'], reverse=True)
			results = []
			for c in candidates[:k]:
				stud_name = None
				if c['student_id']:
					try:
						stud = Student.objects.only('first_name', 'last_name').get(id=c['student_id'])
						stud_name = f"{stud.first_name} {stud.last_name}"
					except Student.DoesNotExist:
						stud_name = None
				results.append({
					'crop_id': c['id'],
					'student_id': c['student_id'],
					'student_name': stud_name,
					'similarity': float(c['similarity']),
					'distance': None,
					'crop_image_path': c['crop_image_path'] or '',
					'is_identified': bool(c['student_id']),
				})
			return results

	@staticmethod
	def auto_assign(
		crop: FaceCrop,
		similarity_threshold: float = 0.6,
		k: int = 5,
		use_voting: bool = False,
		commit: bool = True,
	) -> Dict:
		"""
		Attempt to assign the crop to a student automatically.

		- If use_voting=False: use nearest neighbor only
		- If use_voting=True: use majority vote among top-k identified neighbors
		"""
		if crop.embedding is None:
			return {
				'assigned': False,
				'message': 'This crop has no embedding. Generate embedding first.'
			}

		neighbors = AssignmentService.find_similar_crops(
			crop=crop,
			k=max(1, k),
			embedding_model=crop.embedding_model,
			include_unidentified=True,
		)

		if not neighbors:
			return {
				'assigned': False,
				'message': 'No candidate faces with embeddings were found in this class.'
			}

		chosen_student_id: Optional[int] = None
		confidence: Optional[float] = None

		if not use_voting:
			# Use the single nearest neighbor regardless of identified status
			top = neighbors[0]
			if top.get('student_id') and top.get('similarity', 0.0) >= similarity_threshold:
				chosen_student_id = int(top['student_id'])
				confidence = float(top['similarity'])
		else:
			# Consider only identified neighbors within top-k
			identified = [n for n in neighbors if n.get('student_id')]
			if identified:
				# Group by student and compute average similarity and count
				from collections import defaultdict
				sims = defaultdict(list)
				for n in identified:
					sims[int(n['student_id'])].append(float(n['similarity']))
				# Majority by count, tie-breaker by avg similarity
				best_student = None
				best_count = -1
				best_avg = -1.0
				for sid, arr in sims.items():
					cnt = len(arr)
					avg = sum(arr) / cnt
					if cnt > best_count or (cnt == best_count and avg > best_avg):
						best_student = sid
						best_count = cnt
						best_avg = avg
				if best_student is not None and best_avg >= similarity_threshold:
					chosen_student_id = best_student
					confidence = best_avg

		if chosen_student_id and commit:
			try:
				student = Student.objects.get(id=chosen_student_id)
				crop.identify_student(student, confidence)
			except Student.DoesNotExist:
				chosen_student_id = None

		result = {
			'assigned': chosen_student_id is not None,
			'student_id': chosen_student_id,
			'confidence': confidence,
			'neighbors': neighbors,
		}
		if not result['assigned']:
			# If the nearest neighbor is unassigned and above threshold, inform the caller
			top = neighbors[0]
			if top.get('student_id') is None and top.get('similarity', 0.0) >= similarity_threshold:
				result['message'] = 'Top match has no assigned student. Assignment left empty.'
			else:
				result['message'] = 'No confident match found.'
		return result

	@staticmethod
	def assign_from_candidate(crop: FaceCrop, candidate_crop_id: int, confidence: Optional[float] = None) -> Dict:
		"""
		Assign current crop to the student of the candidate crop if present.
		If candidate has no student, current crop remains unassigned.
		"""
		try:
			candidate = FaceCrop.objects.select_related('student').get(id=candidate_crop_id)
		except FaceCrop.DoesNotExist:
			return {'assigned': False, 'message': f'Candidate crop {candidate_crop_id} not found.'}

		if not candidate.student_id:
			return {'assigned': False, 'message': 'Selected candidate has no student assigned.'}

		crop.identify_student(candidate.student, confidence)
		return {
			'assigned': True,
			'student_id': candidate.student_id,
			'student_name': candidate.student.full_name,
			'confidence': confidence,
		}
