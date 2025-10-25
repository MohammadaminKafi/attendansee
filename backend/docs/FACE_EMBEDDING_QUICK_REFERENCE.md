# Quick Reference: Face Embedding, Clustering & Assignment

## Installation

```bash
# Install dependencies
cd backend
pip install scikit-learn pgvector

# Run migrations
python manage.py migrate attendance

# Verify pgvector extension
python manage.py dbshell
# In psql: SELECT * FROM pg_extension WHERE extname = 'vector';
```

## Quick Start

### 1. Generate Embeddings

```python
# Single crop
POST /api/attendance/face-crops/123/generate-embedding/
{
  "model_name": "facenet"
}

# Multiple crops
POST /api/attendance/face-crops/generate-embeddings-batch/
{
  "face_crop_ids": [1, 2, 3, 4, 5],
  "model_name": "facenet"
}
```

### 2. Cluster Faces

```python
# Session-level
POST /api/attendance/sessions/123/cluster-crops/
{
  "max_clusters": 30,
  "similarity_threshold": 0.5,
  "create_students": true
}

# Class-level
POST /api/attendance/classes/456/cluster-crops/
{
  "max_clusters": 50,
  "similarity_threshold": 0.5,
  "include_identified": false
}
```

### 3. Assign Faces

```python
# Single crop
POST /api/attendance/face-crops/789/assign/
{
  "k": 5,
  "similarity_threshold": 0.6,
  "use_voting": true
}

# Session batch
POST /api/attendance/sessions/123/assign-crops/
{
  "k": 5,
  "similarity_threshold": 0.6
}

# Class batch
POST /api/attendance/classes/456/assign-crops/
{
  "k": 5,
  "similarity_threshold": 0.6
}
```

## Programmatic Usage

### Embedding Service

```python
from attendance.services import EmbeddingService

# Initialize
service = EmbeddingService(model_name='facenet')

# Generate embedding
embedding = service.generate_embedding('/path/to/face.jpg')

# Calculate similarity
similarity = service.calculate_similarity(emb1, emb2)

# Find best match
idx, score = service.find_best_match(query, candidates, threshold=0.6)

# Find top K matches
matches = service.find_top_k_matches(query, candidates, k=5)
```

### Clustering Service

```python
from attendance.services import FaceCropClusteringService

# Initialize
service = FaceCropClusteringService(
    embedding_model='facenet',
    max_clusters=50,
    similarity_threshold=0.5
)

# Cluster session
result = service.cluster_session_crops(
    session_id=123,
    create_students=True,
    assign_crops=True
)

# Cluster class
result = service.cluster_class_crops(
    class_id=456,
    create_students=True,
    assign_crops=True,
    include_identified=False
)
```

### Assignment Service

```python
from attendance.services import FaceCropAssignmentService

# Initialize
service = FaceCropAssignmentService(
    embedding_model='facenet',
    k=5,
    similarity_threshold=0.6,
    use_voting=True
)

# Assign single crop
result = service.assign_crop(crop_id=789, auto_commit=True)

# Assign session crops
result = service.assign_session_crops(session_id=123, auto_commit=True)

# Assign class crops
result = service.assign_class_crops(class_id=456, auto_commit=True)
```

## Model Selection

| Model | Dimensions | Speed | Accuracy | Use Case |
|-------|-----------|-------|----------|----------|
| FaceNet | 128 | Fast | Good | General use, real-time |
| ArcFace | 512 | Slower | Better | High-precision matching |

## Parameter Guidelines

### Clustering

| Parameter | Low | Medium | High | Effect |
|-----------|-----|--------|------|--------|
| max_clusters | 10-20 | 30-50 | 60-100 | More clusters = finer grouping |
| similarity_threshold | 0.3-0.4 | 0.5-0.6 | 0.7-0.8 | Higher = stricter matching |

### Assignment

| Parameter | Low | Medium | High | Effect |
|-----------|-----|--------|------|--------|
| k | 3 | 5-7 | 10-15 | More neighbors = more stable |
| similarity_threshold | 0.4-0.5 | 0.6-0.7 | 0.8-0.9 | Higher = only confident matches |

## Common Workflows

### New Class Setup
1. Process first session images
2. Cluster crops (high threshold for precision)
3. Review and rename students
4. Process subsequent sessions
5. Assign crops using KNN

### Existing Class
1. Process session images
2. Assign crops using KNN
3. Review unassigned crops
4. Manually assign or cluster remaining

### Accuracy Improvement
1. Review misassigned crops
2. Re-cluster entire class
3. Manually verify cluster assignments
4. Re-run assignment with higher threshold

## Debugging

### Check Embeddings
```python
from attendance.models import FaceCrop

crop = FaceCrop.objects.get(id=123)
print(f"Has embedding: {crop.embedding is not None}")
print(f"Model: {crop.embedding_model}")
print(f"Dimension: {len(crop.embedding) if crop.embedding else 0}")
```

### Test Similarity
```python
from attendance.services import EmbeddingService
import numpy as np

service = EmbeddingService()

crop1 = FaceCrop.objects.get(id=123)
crop2 = FaceCrop.objects.get(id=456)

emb1 = FaceEmbedding(vector=np.array(crop1.embedding), model_name='facenet')
emb2 = FaceEmbedding(vector=np.array(crop2.embedding), model_name='facenet')

similarity = service.calculate_similarity(emb1, emb2)
print(f"Similarity: {similarity:.2f}")
```

### Verify Clustering
```python
from attendance.services import ClusteringService

embeddings = [np.array(crop.embedding) for crop in crops]

service = ClusteringService(max_clusters=20, similarity_threshold=0.5)
result = service.cluster_embeddings(embeddings)

print(f"Clusters: {result.num_clusters}")
print(f"Sizes: {result.cluster_sizes}")
```

## Performance Tips

1. **Batch Operations**: Always prefer batch endpoints for multiple crops
2. **Cache Embeddings**: Generate once, use many times
3. **Index Usage**: Database indexes for embeddings are automatic
4. **Session-level**: Process by session, not entire class at once
5. **Model Choice**: Use FaceNet unless accuracy is critical

## Error Handling

```python
try:
    result = service.assign_crop(crop_id=123)
except ValueError as e:
    print(f"Validation error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except RuntimeError as e:
    print(f"Service error: {e}")
```

## Testing

```bash
# Run specific tests
pytest backend/attendance/tests/test_embedding_service.py -v

# With coverage
pytest --cov=attendance.services --cov-report=term

# Single test
pytest backend/attendance/tests/test_clustering_service.py::TestClusteringService::test_cluster_multiple_embeddings -v
```

## Configuration Examples

### High Precision Setup
```python
{
  "embedding_model": "arcface",
  "max_clusters": 30,
  "similarity_threshold": 0.7,
  "k": 7,
  "use_voting": true
}
```

### Fast Processing Setup
```python
{
  "embedding_model": "facenet",
  "max_clusters": 50,
  "similarity_threshold": 0.5,
  "k": 3,
  "use_voting": false
}
```

### Balanced Setup (Recommended)
```python
{
  "embedding_model": "facenet",
  "max_clusters": 40,
  "similarity_threshold": 0.6,
  "k": 5,
  "use_voting": true
}
```
