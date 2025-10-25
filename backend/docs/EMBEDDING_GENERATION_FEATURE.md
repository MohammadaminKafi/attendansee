# Face Embedding Generation Feature

## Summary

A simple implementation for generating face embeddings from face crop images using DeepFace.

## What Was Added

### 1. Embedding Service (`attendance/services/embedding_service.py`)

Simple service class that wraps DeepFace to generate embeddings:

- **`generate_embedding(image_path, model_name)`** - Generates embedding vector for a face crop
- **`get_embedding_dimension(model_name)`** - Returns embedding dimensions for a model
- Supports 3 models: ArcFace (512D), FaceNet (128D), FaceNet512 (512D)

### 2. API Endpoint

Added to `FaceCropViewSet` in `attendance/views.py`:

```
POST /api/attendance/face-crops/{id}/generate-embedding/
```

**Request:**
```json
{
  "model_name": "arcface"  // or "facenet" or "facenet512"
}
```

**Response:**
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

### 3. Serializer

Added `GenerateEmbeddingSerializer` in `attendance/serializers.py`:
- Validates the `model_name` parameter
- Ensures lowercase model names

### 4. Documentation

Created `backend/docs/EMBEDDING_GENERATION_API.md` with:
- Complete API documentation
- Usage examples (cURL, Python, JavaScript)
- Error handling
- Integration notes

## Files Modified

- ✅ `attendance/services/embedding_service.py` (created)
- ✅ `attendance/services/__init__.py` (updated exports)
- ✅ `attendance/serializers.py` (added GenerateEmbeddingSerializer)
- ✅ `attendance/views.py` (added generate_embedding action to FaceCropViewSet)
- ✅ `docs/EMBEDDING_GENERATION_API.md` (created documentation)

## Usage

1. **Upload an image to a session**
2. **Process the image to extract face crops** (using existing face detection)
3. **Generate embedding for a face crop:**

```bash
curl -X POST http://localhost:8000/api/attendance/face-crops/123/generate-embedding/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "arcface"}'
```

4. **The embedding is saved to the database** in the `FaceCrop.embedding` field

## Model Information

| Model | Dimensions | Use Case |
|-------|-----------|----------|
| ArcFace | 512 | Best accuracy (default) |
| FaceNet | 128 | Faster, smaller |
| FaceNet512 | 512 | Balance of speed and accuracy |

## Database Fields Updated

When embedding is generated, these `FaceCrop` fields are updated:
- `embedding` - Vector field storing the embedding
- `embedding_model` - String indicating which model was used
- `updated_at` - Timestamp

## Next Steps

With embeddings generated, you can now implement:
- Face similarity search
- Automatic student identification
- Face clustering
- Cross-session face matching

## Requirements

Make sure DeepFace is installed:
```bash
pip install deepface
```

## Simple & Clean

This implementation follows the requirements:
- ✅ Simple code without complexity
- ✅ Uses DeepFace with minimal configuration
- ✅ Supports ArcFace, FaceNet, and FaceNet512
- ✅ Main logic in services
- ✅ Clean API endpoint
- ✅ No complicated features
