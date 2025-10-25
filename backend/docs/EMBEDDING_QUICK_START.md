# Quick Start: Face Embedding Generation

## Overview
Simple API to generate face embeddings for face crops using DeepFace.

## Endpoint

```
POST /api/attendance/face-crops/{id}/generate-embedding/
```

## Request

```json
{
  "model_name": "arcface"
}
```

**Options:**
- `"arcface"` - 512 dimensions (default, best accuracy)
- `"facenet"` - 128 dimensions (faster)
- `"facenet512"` - 512 dimensions (balanced)

## Response

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

## Example Usage

### cURL
```bash
curl -X POST http://localhost:8000/api/attendance/face-crops/123/generate-embedding/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "arcface"}'
```

### Python
```python
import requests

url = "http://localhost:8000/api/attendance/face-crops/123/generate-embedding/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.post(url, headers=headers, json={"model_name": "arcface"})
print(response.json())
```

## What Gets Updated

The `FaceCrop` model fields:
- `embedding` - The vector (stored in PostgreSQL)
- `embedding_model` - Model name used
- `updated_at` - Timestamp

## Implementation

- **Service:** `attendance/services/embedding_service.py`
- **View:** `attendance/views.py` (FaceCropViewSet.generate_embedding)
- **Serializer:** `attendance/serializers.py` (GenerateEmbeddingSerializer)

## Full Documentation

See `EMBEDDING_GENERATION_API.md` for complete API documentation.
