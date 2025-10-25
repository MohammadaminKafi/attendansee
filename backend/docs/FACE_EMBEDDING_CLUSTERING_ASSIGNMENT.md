# Face Embedding, Clustering, and Assignment Features

This document describes the new functionality added to the AttendanSee backend for face embedding generation, clustering, and automatic assignment using similarity search.

## Overview

The system now supports:
1. **Face Embedding Generation** - Generate embeddings using FaceNet (128D) or ArcFace (512D)
2. **Face Clustering** - Automatically group similar faces and create student records
3. **Face Assignment** - Assign face crops to students using KNN similarity search

## Architecture

### Services Layer (`backend/attendance/services/`)

#### 1. Embedding Service (`embedding_service.py`)
Generates face embeddings using deep learning models.

**Key Classes:**
- `FaceEmbedding` - Data class for embedding vectors
- `EmbeddingModel` - Abstract base for embedding models
- `FaceNetModel` - FaceNet implementation (128 dimensions)
- `ArcFaceModel` - ArcFace implementation (512 dimensions)
- `EmbeddingModelFactory` - Factory for creating model instances
- `EmbeddingService` - Main service for embedding operations

**Design Patterns:**
- Strategy Pattern for model selection
- Factory Pattern for model instantiation
- Service Layer for high-level operations

**Example Usage:**
```python
from attendance.services import EmbeddingService

# Generate embedding
service = EmbeddingService(model_name='facenet')
embedding = service.generate_embedding('/path/to/face.jpg')

# Calculate similarity
similarity = service.calculate_similarity(embedding1, embedding2)

# Find best match
best_idx, score = service.find_best_match(query_emb, candidates)
```

#### 2. Clustering Service (`clustering_service.py`)
Clusters face crops using embeddings.

**Key Classes:**
- `ClusterResult` - Data class for clustering results
- `ClusteringService` - Low-level clustering operations
- `FaceCropClusteringService` - High-level Django integration

**Features:**
- Agglomerative clustering with distance threshold
- Automatic embedding generation
- Student record creation for clusters
- Support for max clusters constraint
- DBSCAN for noise detection

**Example Usage:**
```python
from attendance.services import FaceCropClusteringService

service = FaceCropClusteringService(
    embedding_model='facenet',
    max_clusters=50,
    similarity_threshold=0.5
)

# Cluster session crops
result = service.cluster_session_crops(
    session_id=123,
    create_students=True,
    assign_crops=True
)
```

#### 3. Assignment Service (`assignment_service.py`)
Assigns face crops to students using KNN.

**Key Classes:**
- `AssignmentResult` - Data class for assignment results
- `AssignmentService` - KNN similarity search
- `FaceCropAssignmentService` - High-level Django integration

**Features:**
- K-Nearest Neighbors search
- Cosine similarity matching
- Majority voting support
- Configurable similarity threshold
- Batch assignment

**Example Usage:**
```python
from attendance.services import FaceCropAssignmentService

service = FaceCropAssignmentService(
    embedding_model='facenet',
    k=5,
    similarity_threshold=0.6,
    use_voting=True
)

# Assign single crop
result = service.assign_crop(crop_id=456, auto_commit=True)

# Assign all crops in session
result = service.assign_session_crops(session_id=123)
```

## Database Schema

### FaceCrop Model Updates

New fields added:
```python
embedding = VectorField(
    dimensions=512,
    null=True,
    blank=True
)

embedding_model = CharField(
    max_length=20,
    choices=[
        ('facenet', 'FaceNet (128D)'),
        ('arcface', 'ArcFace (512D)')
    ],
    null=True,
    blank=True
)
```

### Migration

File: `backend/attendance/migrations/0003_enable_pgvector_add_embedding_fields.py`

This migration:
- Enables pgvector extension
- Adds embedding vector field
- Adds embedding_model field
- Creates indexes for efficient similarity search (HNSW)

**To apply:**
```bash
cd backend
python manage.py migrate attendance
```

## API Endpoints

### Embedding Generation

#### Generate Single Embedding
**POST** `/api/attendance/face-crops/{id}/generate-embedding/`

Parameters:
- `model_name` (optional): 'facenet' or 'arcface' (default: 'facenet')
- `force_regenerate` (optional): boolean (default: false)

Response:
```json
{
  "status": "success",
  "crop_id": 123,
  "embedding_model": "facenet",
  "embedding_dimension": 128,
  "message": "Embedding generated successfully"
}
```

#### Generate Batch Embeddings
**POST** `/api/attendance/face-crops/generate-embeddings-batch/`

Parameters:
- `face_crop_ids`: list of integers (required)
- `model_name` (optional): 'facenet' or 'arcface'
- `force_regenerate` (optional): boolean

Response:
```json
{
  "status": "completed",
  "total": 10,
  "success": 9,
  "skipped": 1,
  "errors": 0,
  "model_name": "facenet",
  "results": [...]
}
```

### Clustering

#### Cluster Session Crops
**POST** `/api/attendance/sessions/{id}/cluster-crops/`

Parameters:
- `max_clusters` (optional): integer, 1-200 (default: 50)
- `similarity_threshold` (optional): float, 0-1 (default: 0.5)
- `embedding_model` (optional): 'facenet' or 'arcface'
- `create_students` (optional): boolean (default: true)
- `assign_crops` (optional): boolean (default: true)

Response:
```json
{
  "status": "success",
  "session_id": 123,
  "session_name": "Session 1",
  "clusters_found": 15,
  "students_created": 15,
  "crops_assigned": 45,
  "cluster_sizes": {
    "0": 5,
    "1": 3,
    ...
  }
}
```

#### Cluster Class Crops
**POST** `/api/attendance/classes/{id}/cluster-crops/`

Parameters: Same as session clustering plus:
- `include_identified` (optional): boolean (default: false)

Response: Similar to session clustering

### Assignment

#### Assign Single Crop
**POST** `/api/attendance/face-crops/{id}/assign/`

Parameters:
- `k` (optional): integer, 1-20 (default: 5)
- `similarity_threshold` (optional): float, 0-1 (default: 0.6)
- `embedding_model` (optional): 'facenet' or 'arcface'
- `use_voting` (optional): boolean (default: true)
- `auto_commit` (optional): boolean (default: true)

Response:
```json
{
  "status": "assigned",
  "crop_id": 123,
  "student_id": 45,
  "student_name": "John Doe",
  "confidence": 0.85,
  "k_nearest": [
    {
      "student_id": 45,
      "student_name": "John Doe",
      "similarity": 0.85
    },
    ...
  ]
}
```

#### Assign Session Crops (Batch)
**POST** `/api/attendance/sessions/{id}/assign-crops/`

Parameters: Same as single assignment

Response:
```json
{
  "status": "completed",
  "session_id": 123,
  "total_crops": 20,
  "assigned": 18,
  "no_match": 2,
  "errors": 0,
  "parameters": {...}
}
```

#### Assign Class Crops (Batch)
**POST** `/api/attendance/classes/{id}/assign-crops/`

Parameters: Same as single assignment

Response: Similar to session assignment

## Workflow Examples

### Scenario 1: First-time Session Processing

1. **Detect faces and create crops** (existing functionality)
   ```
   POST /api/attendance/images/{id}/process-image/
   ```

2. **Cluster the face crops to identify unique students**
   ```
   POST /api/attendance/sessions/{id}/cluster-crops/
   {
     "max_clusters": 30,
     "similarity_threshold": 0.5,
     "create_students": true,
     "assign_crops": true
   }
   ```

3. **Review and rename automatically created students**
   - Students are created with names like "Class_Math101_Session_1_Cluster_1"
   - Manually rename to actual student names via student update endpoints

### Scenario 2: Subsequent Sessions with Existing Students

1. **Process images to detect faces**
   ```
   POST /api/attendance/images/{id}/process-image/
   ```

2. **Assign crops to existing students using KNN**
   ```
   POST /api/attendance/sessions/{id}/assign-crops/
   {
     "k": 5,
     "similarity_threshold": 0.6,
     "use_voting": true
   }
   ```

3. **Review unassigned crops and manually assign or cluster**

### Scenario 3: Class-wide Re-clustering

For improving accuracy across all sessions:

```
POST /api/attendance/classes/{id}/cluster-crops/
{
  "max_clusters": 50,
  "similarity_threshold": 0.5,
  "include_identified": true,
  "create_students": true
}
```

## Configuration

### Embedding Models

**FaceNet (128D)**
- Faster generation
- Lower memory usage
- Good for real-time applications
- Recommended for most use cases

**ArcFace (512D)**
- Higher accuracy
- More memory intensive
- Better for high-precision matching
- Recommended when accuracy is critical

### Clustering Parameters

**max_clusters**
- Controls maximum number of clusters
- Higher = more granular grouping
- Lower = more faces grouped together
- Recommended: 30-50 for typical class sizes

**similarity_threshold**
- Controls how similar faces must be to group together
- Higher (0.7-0.9) = stricter, more clusters
- Lower (0.4-0.6) = looser, fewer clusters
- Recommended: 0.5-0.6 for general use

### Assignment Parameters

**k (K-Nearest Neighbors)**
- Number of neighbors to consider
- Higher = more stable but slower
- Lower = faster but less robust
- Recommended: 5-7

**similarity_threshold**
- Minimum similarity to make assignment
- Higher = only confident matches
- Lower = more matches but less accurate
- Recommended: 0.6-0.7

**use_voting**
- true: Use majority voting (more robust)
- false: Use best match only (faster)
- Recommended: true

## Dependencies

Added to `backend/pyproject.toml`:
- `pgvector>=0.4.1` - PostgreSQL vector extension
- `scikit-learn>=1.3.0` - Clustering algorithms
- `deepface>=0.0.93` - Face embedding models (already present)
- `numpy>=1.26.0` - Numerical operations (already present)

## Testing

### Run All Tests
```bash
cd backend
pytest attendance/tests/test_embedding_service.py -v
pytest attendance/tests/test_clustering_service.py -v
pytest attendance/tests/test_assignment_service.py -v
pytest attendance/tests/test_new_embedding_clustering_assignment_endpoints.py -v
```

### Test Coverage
```bash
pytest --cov=attendance.services --cov-report=html
```

## Performance Considerations

1. **Embedding Generation**
   - First-time: ~1-2 seconds per face crop
   - Cached: Instant (stored in database)
   - Batch processing recommended

2. **Clustering**
   - Time complexity: O(n²) for similarity matrix
   - Recommended: Process per session (<100 faces)
   - For large classes: Use class-level clustering sparingly

3. **Assignment**
   - Time complexity: O(k*n) per crop
   - Fast with indexed embeddings
   - Batch processing is efficient

## Troubleshooting

### Issue: Embeddings not generating
- Check if face crop image files exist on disk
- Verify DeepFace models are downloaded
- Check logs for specific errors

### Issue: Poor clustering results
- Adjust similarity_threshold (try 0.4-0.7 range)
- Use ArcFace for better accuracy
- Ensure good quality face crops

### Issue: Low assignment confidence
- Generate more identified crops per student
- Use higher k value (7-10)
- Lower similarity_threshold slightly

### Issue: Database errors with vectors
- Ensure pgvector extension is installed
- Run migrations: `python manage.py migrate`
- Check PostgreSQL version (>=11 required)

## Future Enhancements

Potential improvements:
1. Face recognition confidence scores per model
2. Active learning for improving models
3. Real-time clustering updates
4. GPU acceleration support
5. Face quality assessment before embedding
6. Temporal consistency (tracking across sessions)

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [DeepFace Repository](https://github.com/serengil/deepface)
- [FaceNet Paper](https://arxiv.org/abs/1503.03832)
- [ArcFace Paper](https://arxiv.org/abs/1801.07698)
