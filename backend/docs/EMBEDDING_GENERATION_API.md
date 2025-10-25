# Face Embedding Generation API

## Overview

This document describes the simple API for generating face embeddings from face crop images using DeepFace.

## Service

### EmbeddingService

Location: `attendance/services/embedding_service.py`

Simple service that provides face embedding generation using DeepFace.

**Supported Models:**
- `arcface` - ArcFace model (512 dimensions)
- `facenet` - FaceNet model (128 dimensions)  
- `facenet512` - FaceNet512 model (512 dimensions)

**Methods:**

```python
generate_embedding(image_path: str, model_name: str = 'arcface') -> List[float]
```
- Generates embedding vector for a face crop image
- Returns list of floats representing the embedding
- Raises FileNotFoundError if image doesn't exist
- Raises ValueError if model is not supported

```python
get_embedding_dimension(model_name: str) -> int
```
- Returns the embedding dimension for a given model

## API Endpoint

### Generate Embedding for Face Crop

**Endpoint:** `POST /api/attendance/face-crops/{id}/generate-embedding/`

**Description:** Generates a face embedding vector for a specific face crop and saves it to the database.

**Authentication:** Required (IsAuthenticated + IsClassOwnerOrAdmin)

**URL Parameters:**
- `id` (integer, required) - The ID of the face crop

**Request Body:**
```json
{
  "model_name": "arcface"
}
```

**Fields:**
- `model_name` (string, optional) - Model to use for embedding generation
  - Choices: `"arcface"`, `"facenet"`, `"facenet512"`
  - Default: `"arcface"`

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Embedding generated successfully",
  "face_crop_id": 123,
  "model_name": "arcface",
  "embedding_dimension": 512,
  "embedding_preview": [0.123, -0.456, 0.789, 0.234, -0.567],
  "has_embedding": true
}
```

**Error Responses:**

- **400 Bad Request** - Invalid model name
```json
{
  "error": "Unsupported model: invalid_model. Supported models: ['arcface', 'facenet', 'facenet512']"
}
```

- **404 Not Found** - Face crop image not found
```json
{
  "error": "Face crop image not found"
}
```

- **500 Internal Server Error** - Failed to generate embedding
```json
{
  "error": "Failed to generate embedding",
  "details": "Error message details"
}
```

## Usage Examples

### Using cURL

```bash
# Generate embedding using ArcFace (default)
curl -X POST http://localhost:8000/api/attendance/face-crops/123/generate-embedding/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Generate embedding using FaceNet
curl -X POST http://localhost:8000/api/attendance/face-crops/123/generate-embedding/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "facenet"}'

# Generate embedding using FaceNet512
curl -X POST http://localhost:8000/api/attendance/face-crops/123/generate-embedding/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "facenet512"}'
```

### Using Python Requests

```python
import requests

# API endpoint
url = "http://localhost:8000/api/attendance/face-crops/123/generate-embedding/"

# Headers with authentication
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

# Generate embedding with ArcFace
response = requests.post(url, headers=headers, json={"model_name": "arcface"})
data = response.json()

print(f"Status: {data['status']}")
print(f"Model: {data['model_name']}")
print(f"Dimension: {data['embedding_dimension']}")
print(f"Preview: {data['embedding_preview']}")
```

### Using JavaScript/Fetch

```javascript
// Generate embedding for face crop
const faceCropId = 123;
const response = await fetch(
  `http://localhost:8000/api/attendance/face-crops/${faceCropId}/generate-embedding/`,
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model_name: 'arcface'
    })
  }
);

const data = await response.json();
console.log('Embedding generated:', data);
```

## Database Storage

When an embedding is generated, the following fields in the `FaceCrop` model are updated:

- `embedding` (VectorField) - The embedding vector (up to 512 dimensions)
- `embedding_model` (CharField) - The model name used to generate the embedding
- `updated_at` (DateTimeField) - Timestamp of the update

## Notes

- The face crop image must exist on the server before generating an embedding
- DeepFace must be installed: `pip install deepface`
- The embedding is stored as a PostgreSQL vector using pgvector extension
- Only one face should be present in the face crop image
- Embeddings can be regenerated with different models at any time
- Previously generated embeddings will be overwritten when regenerating

## Integration with Face Recognition

The generated embeddings can be used for:
- Face similarity search
- Student identification
- Clustering similar faces
- Cross-session face matching

Future endpoints will utilize these embeddings for automated face recognition tasks.
