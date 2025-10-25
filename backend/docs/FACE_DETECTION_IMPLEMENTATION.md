# Face Detection and Image Processing Implementation

## Overview

This document describes the complete implementation of face detection and image processing functionality in the AttendanSee backend. This implementation is **independent of the core module** and follows best practices and design patterns.

## Architecture

### Service Layer

The implementation follows a **service-oriented architecture** with two main services:

1. **FaceDetectionService** (`attendance/services/face_detection.py`)
   - Detects faces in images using DeepFace
   - Extracts face crops with coordinates
   - Provides clean abstraction over DeepFace library
   - Supports multiple detector backends (retinaface, opencv, mtcnn, etc.)

2. **ImageProcessor** (`attendance/services/image_processor.py`)
   - Draws rectangles around detected faces
   - Applies grayscale/shadow effects to non-face regions
   - Saves processed images
   - Supports method chaining for fluent API

### Design Patterns Used

1. **Strategy Pattern**: Different face detector backends can be swapped easily
2. **Dependency Injection**: Services accept dependencies as parameters
3. **Single Responsibility Principle**: Each class has one clear purpose
4. **Builder/Fluent Interface**: Methods return `self` for chaining
5. **Factory Pattern**: Static methods for one-call processing

## Implementation Details

### 1. Face Detection Service

**Location**: `attendance/services/face_detection.py`

**Key Features**:
- Supports 9 different detector backends
- Returns structured `FaceDetection` objects
- Handles errors gracefully
- Lazy-loads DeepFace to avoid import overhead

**Example Usage**:
```python
from attendance.services import FaceDetectionService

# Initialize service
service = FaceDetectionService(detector_backend='retinaface')

# Detect faces
detections = service.detect_faces('/path/to/image.jpg', min_confidence=0.7)

# Extract and save crops
crops = service.detect_and_extract_crops(
    image_path='/path/to/image.jpg',
    output_dir='/path/to/crops',
    min_confidence=0.7
)
```

**FaceDetection DataClass**:
- `facial_area`: Dict with x, y, w, h coordinates
- `confidence`: Detection confidence (0-1)
- `face_image`: Optional numpy array of the face
- Properties: `x`, `y`, `w`, `h`, `coordinates_string`, `bounding_box`

### 2. Image Processor Service

**Location**: `attendance/services/image_processor.py`

**Key Features**:
- Draws green rectangles around faces
- Applies grayscale + darkening to non-face regions
- Supports custom colors and parameters
- Method chaining for fluent workflow

**Example Usage**:
```python
from attendance.services import ImageProcessor

# Method chaining approach
processor = ImageProcessor()
processor.load_image('/path/to/image.jpg')
         .draw_face_rectangles(detections)
         .apply_background_effect()
         .save('/path/to/output.jpg')

# Or use the static method
ImageProcessor.process_image_with_faces(
    input_path='/path/to/image.jpg',
    output_path='/path/to/output.jpg',
    detections=detections,
    apply_background=True
)
```

### 3. Utility Functions

**Location**: `attendance/utils.py`

**Main Function**: `process_image_with_face_detection()`

This is the primary entry point used by the API. It orchestrates the entire processing workflow:

1. Validates the image file exists
2. Detects faces using FaceDetectionService
3. Creates processed image with ImageProcessor
4. Saves processed image to the database
5. Extracts and saves individual face crops
6. Creates FaceCrop database records
7. Updates Image and Session processing status

**Example Usage**:
```python
from attendance.utils import process_image_with_face_detection

result = process_image_with_face_detection(
    image_obj=my_image,
    detector_backend='retinaface',
    min_confidence=0.7,
    apply_background_effect=True
)

print(f"Found {result['faces_detected']} faces")
print(f"Created crops: {result['crops_created']}")
```

### 4. API Endpoint

**Endpoint**: `POST /api/attendance/images/{id}/process-image/`

**Parameters** (optional):
- `min_face_size`: Minimum face size in pixels (default: 20)
- `confidence_threshold`: Confidence threshold for detection (default: 0.5)

**Response**:
```json
{
    "status": "completed",
    "image_id": 123,
    "session_id": 45,
    "class_id": 12,
    "faces_detected": 3,
    "crops_created": [101, 102, 103],
    "processed_image_url": "/media/processed_images/...",
    "message": "Image processed successfully"
}
```

**Authentication**: Required
**Permissions**: User must own the class or be an admin

## Database Changes

No database migrations required! The implementation uses the existing models:

- **Image**: Stores original and processed images
- **FaceCrop**: Stores individual face crops with coordinates
- **Session**: Tracks processing status

## Testing

### Test Coverage

The implementation includes **comprehensive tests** covering:

1. **Unit Tests for FaceDetectionService** (`test_face_detection_service.py`)
   - Detection with various backends
   - Coordinate extraction
   - Confidence filtering
   - Error handling
   - Edge cases

2. **Unit Tests for ImageProcessor** (`test_image_processor.py`)
   - Image loading from file and array
   - Rectangle drawing
   - Background effects
   - Method chaining
   - Edge cases (small images, overlapping faces)

3. **Integration Tests** (`test_process_image.py`)
   - End-to-end API workflow
   - Authentication and permissions
   - Database updates
   - Error scenarios
   - Session status updates

4. **Test Helpers** (`test_helpers.py`)
   - Utilities for creating test images
   - Mock face detection objects
   - Context managers for cleanup

### Running Tests

```bash
# Run all tests
cd backend
pytest

# Run specific test file
pytest attendance/tests/test_face_detection_service.py

# Run with coverage
pytest --cov=attendance --cov-report=html

# Run only face detection tests
pytest -k "face_detection"
```

## Dependencies

**Added to `pyproject.toml`**:
- `opencv-python>=4.8.1`: Image processing
- `deepface>=0.0.93`: Face detection
- `tf-keras>=2.18.0`: Backend for DeepFace
- `numpy>=1.26.0`: Array operations

**Installation**:
```bash
cd backend
pip install -e .
```

## Migration from Core Module

The implementation is **fully independent** of the `core/face/extractor.py` module. Here's the migration path:

### Immediate Usage

All new code should use the new services:
```python
# OLD (core dependency)
from core.face.extractor import FaceExtractor
extractor = FaceExtractor()

# NEW (independent backend)
from attendance.services import FaceDetectionService
service = FaceDetectionService()
```

### Backward Compatibility

The `utils.py` includes a deprecated legacy function for backward compatibility:
```python
# This still works but shows deprecation warning
process_image_with_face_detection_legacy(image_obj, extractor)
```

### Complete Migration Steps

1. ✅ **Phase 1**: New services created and tested
2. ✅ **Phase 2**: API updated to use new services
3. ⏳ **Phase 3**: Update any remaining code using core module
4. ⏳ **Phase 4**: Remove core module dependency

## API Documentation

### Process Image

**Endpoint**: `POST /api/attendance/images/{id}/process-image/`

**Description**: Processes an uploaded image to detect faces, create processed image with rectangles and effects, and extract face crops.

**Request Body** (optional):
```json
{
    "min_face_size": 20,
    "confidence_threshold": 0.7
}
```

**Response (Success)**:
```json
{
    "status": "completed",
    "image_id": 123,
    "session_id": 45,
    "class_id": 12,
    "faces_detected": 2,
    "crops_created": [101, 102],
    "processed_image_url": "/media/processed_images/processed_image_123.jpg",
    "message": "Image processed successfully"
}
```

**Response (Error)**:
```json
{
    "error": "Image has already been processed",
    "image_id": 123,
    "processed_date": "2025-10-24T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Processing successful
- `400 Bad Request`: Image already processed or invalid parameters
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Image not found or user doesn't have access
- `500 Internal Server Error`: Processing failed

## Performance Considerations

1. **Face Detection**: Uses RetinaFace by default (most accurate but slower)
   - For faster processing, use `detector_backend='opencv'`
   - Consider processing in background task queue for production

2. **Image Size**: Large images take longer to process
   - Consider resizing images before detection
   - Can be configured per request

3. **Memory**: DeepFace loads models into memory
   - Models are cached after first use
   - Consider memory requirements in deployment

## Future Enhancements

1. **Async Processing**: Move to Celery for background processing
2. **Face Recognition**: Match detected faces to known students
3. **Batch Processing**: Process multiple images at once
4. **Custom Models**: Support for custom trained models
5. **Face Quality**: Add face quality assessment
6. **Multiple Backends**: Fallback to different backends on failure

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'cv2'**
   ```bash
   pip install opencv-python
   ```

2. **ImportError: No module named 'deepface'**
   ```bash
   pip install deepface tf-keras
   ```

3. **No faces detected in image**
   - Try different detector backend
   - Lower confidence threshold
   - Check image quality and resolution
   - Ensure faces are clearly visible

4. **Memory errors**
   - Reduce image size before processing
   - Use lighter detector backend (opencv, ssd)
   - Increase system memory

## Contact and Support

For issues or questions:
1. Check test files for usage examples
2. Review service docstrings
3. Check existing tests for similar scenarios

## Summary

This implementation provides a **production-ready, well-tested, independent** face detection and image processing system for the AttendanSee backend. It follows SOLID principles, includes comprehensive tests, and is ready for immediate use.

Key achievements:
- ✅ Complete independence from core module
- ✅ Clean service-oriented architecture
- ✅ Comprehensive test coverage (unit + integration)
- ✅ Well-documented with examples
- ✅ Handles errors gracefully
- ✅ Production-ready API endpoint
- ✅ Backward compatible during migration
