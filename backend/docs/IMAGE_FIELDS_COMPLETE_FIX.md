# Image Field Migration - Complete Fix

## Summary
Converted all image path fields from CharField to ImageField for proper file handling across the entire system:
- `Image.original_image_path` (already done)
- `Image.processed_image_path` (fixed)
- `FaceCrop.crop_image_path` (fixed)

## Model Changes

### 1. Image Model
**File**: `backend/attendance/models.py`

#### Before
```python
original_image_path = models.CharField(max_length=500)
processed_image_path = models.CharField(max_length=500, blank=True, default='')
```

#### After
```python
original_image_path = models.ImageField(upload_to='session_images/', max_length=500)
processed_image_path = models.ImageField(upload_to='processed_images/', max_length=500, blank=True, null=True)
```

**Changes:**
- `original_image_path`: Now an ImageField for uploaded session images
- `processed_image_path`: Now an ImageField for processed images with face rectangles, nullable instead of default empty string

### 2. FaceCrop Model
**File**: `backend/attendance/models.py`

#### Before
```python
crop_image_path = models.CharField(max_length=500)
```

#### After
```python
crop_image_path = models.ImageField(upload_to='face_crops/', max_length=500)
```

**Changes:**
- `crop_image_path`: Now an ImageField for extracted face crop images

## File Organization

Images will be organized in the media directory:
```
media/
├── session_images/        # Original uploaded images
├── processed_images/      # Images with face detection rectangles
└── face_crops/            # Individual face crop images
```

## New Utility Module

**File**: `backend/attendance/utils.py` (created)

### Functions Provided

#### 1. `save_processed_image(image_obj, processed_file_path)`
Saves a processed image file to an Image instance.

**Usage:**
```python
from attendance.utils import save_processed_image

save_processed_image(image_obj, "/path/to/processed_image.jpg")
```

#### 2. `save_face_crop(face_crop_obj, crop_file_path)`
Saves a face crop image file to a FaceCrop instance.

**Usage:**
```python
from attendance.utils import save_face_crop

save_face_crop(face_crop_obj, "/path/to/face_crop.jpg")
```

#### 3. `create_face_crop_from_file(...)`
Creates a new FaceCrop instance from a file.

**Usage:**
```python
from attendance.utils import create_face_crop_from_file

face_crop = create_face_crop_from_file(
    image_obj=image_instance,
    crop_file_path="/path/to/crop.jpg",
    coordinates="100,150,200,250",
    confidence_score=0.95,
    student=student_instance  # Optional
)
```

#### 4. `process_image_with_face_detection(...)`
Complete integration with the core face recognition module.

**Usage:**
```python
from attendance.utils import process_image_with_face_detection

result = process_image_with_face_detection(
    image_obj=image_instance,
    min_face_size=20,
    confidence_threshold=0.5
)

# result = {
#     'faces_detected': 3,
#     'crops_created': [1, 2, 3],  # FaceCrop IDs
#     'processed_image_url': '/media/processed_images/image.jpg'
# }
```

## Updated API Endpoint

### POST `/api/attendance/images/{id}/process-image/`

**Description:** Process an uploaded image to detect faces and create crops.

**Request Body (optional):**
```json
{
  "min_face_size": 20,
  "confidence_threshold": 0.5
}
```

**Success Response (200):**
```json
{
  "status": "completed",
  "image_id": 123,
  "session_id": 5,
  "class_id": 2,
  "faces_detected": 3,
  "crops_created": [45, 46, 47],
  "processed_image_url": "/media/processed_images/image_123.jpg",
  "message": "Image processed successfully"
}
```

**Error Response (400 - Already Processed):**
```json
{
  "error": "Image has already been processed",
  "image_id": 123,
  "processed_date": "2025-10-23T10:30:00Z"
}
```

**Error Response (500 - Processing Failed):**
```json
{
  "error": "Failed to process image",
  "details": "Face detection error message"
}
```

## Migration Steps

### 1. Create Migration
```bash
cd backend
python manage.py makemigrations
```

This will create a migration that:
- Changes `Image.processed_image_path` from CharField to ImageField
- Changes `FaceCrop.crop_image_path` from CharField to ImageField
- Converts existing string paths to ImageField references (if any data exists)

### 2. Review Migration
Check the generated migration file in `backend/attendance/migrations/`.

### 3. Apply Migration
```bash
python manage.py migrate
```

### 4. Handle Existing Data (if any)
If you have existing data with file paths stored as strings:

```python
# Run this in Django shell (python manage.py shell)
from attendance.models import Image, FaceCrop
from django.core.files import File
import os

# Migrate existing processed images
for img in Image.objects.exclude(processed_image_path=''):
    old_path = str(img.processed_image_path)
    if os.path.exists(old_path):
        with open(old_path, 'rb') as f:
            img.processed_image_path.save(
                os.path.basename(old_path),
                File(f),
                save=True
            )

# Migrate existing face crops
for crop in FaceCrop.objects.all():
    old_path = str(crop.crop_image_path)
    if os.path.exists(old_path):
        with open(old_path, 'rb') as f:
            crop.crop_image_path.save(
                os.path.basename(old_path),
                File(f),
                save=True
            )
```

## API Response Changes

### Image Serializer
**Before:**
```json
{
  "id": 123,
  "original_image_path": "/some/path/image.jpg",
  "processed_image_path": "/some/path/processed.jpg"
}
```

**After:**
```json
{
  "id": 123,
  "original_image_path": "/media/session_images/image.jpg",
  "processed_image_path": "/media/processed_images/processed.jpg"
}
```

### FaceCrop Serializer
**Before:**
```json
{
  "id": 45,
  "crop_image_path": "/some/path/crop.jpg",
  "coordinates": "100,150,200,250"
}
```

**After:**
```json
{
  "id": 45,
  "crop_image_path": "/media/face_crops/crop.jpg",
  "coordinates": "100,150,200,250"
}
```

## Frontend Integration

### Displaying Processed Images
```typescript
// In SessionDetailPage or similar component
const processedImageUrl = `${API_BASE_URL.replace('/api', '')}${image.processed_image_path}`;

<img src={processedImageUrl} alt="Processed" />
```

### Displaying Face Crops
```typescript
// In a face crops list component
const cropImageUrl = `${API_BASE_URL.replace('/api', '')}${faceCrop.crop_image_path}`;

<img src={cropImageUrl} alt="Face crop" />
```

### Processing an Image
```typescript
// Call the process endpoint after upload
const processImage = async (imageId: number) => {
  try {
    const response = await api.post(
      `/attendance/images/${imageId}/process-image/`,
      {
        min_face_size: 20,
        confidence_threshold: 0.5
      }
    );
    
    console.log('Faces detected:', response.data.faces_detected);
    console.log('Crops created:', response.data.crops_created);
  } catch (error) {
    console.error('Processing failed:', error);
  }
};
```

## Benefits of ImageField

1. **Automatic URL Generation**: Django generates proper URLs for file access
2. **File Validation**: Validates that uploaded files are actually images
3. **Storage Backend**: Can easily switch to cloud storage (S3, etc.) later
4. **File Management**: Handles file deletion when model instances are deleted
5. **Consistent API**: All image paths follow the same pattern
6. **Media Serving**: Works seamlessly with Django's media serving

## Testing Checklist

- [ ] Upload a new image to a session
- [ ] Process the image using the `/process-image/` endpoint
- [ ] Verify processed image is saved correctly
- [ ] Verify face crops are created with proper images
- [ ] Check that all image URLs are accessible
- [ ] Verify images display correctly in frontend
- [ ] Test image deletion (should remove files from disk)
- [ ] Check permissions (users can only process their own class images)

## Production Considerations

### 1. Cloud Storage
For production, configure django-storages with S3:

```python
# settings.py
INSTALLED_APPS += ['storages']

AWS_ACCESS_KEY_ID = 'your-key'
AWS_SECRET_ACCESS_KEY = 'your-secret'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-east-1'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### 2. Image Processing Queue
For large-scale deployments, process images asynchronously:

```python
# Use Celery for background processing
@shared_task
def process_image_task(image_id):
    image_obj = Image.objects.get(id=image_id)
    process_image_with_face_detection(image_obj)
```

### 3. File Size Limits
Add validation in settings:

```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

### 4. Image Optimization
Consider adding image compression:

```python
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def optimize_image(image_field, max_size=(1920, 1080), quality=85):
    img = PILImage.open(image_field)
    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
    
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality)
    output.seek(0)
    
    return InMemoryUploadedFile(
        output, 'ImageField', 
        f"{image_field.name.split('.')[0]}.jpg",
        'image/jpeg', output.getbuffer().nbytes, None
    )
```

## Related Files Modified

1. `backend/attendance/models.py` - Model field changes
2. `backend/attendance/views.py` - Updated process_image endpoint
3. `backend/attendance/utils.py` - New utility functions (created)
4. `backend/attendansee_backend/settings.py` - Media configuration (already done)
5. `backend/attendansee_backend/urls.py` - Media URL serving (already done)
