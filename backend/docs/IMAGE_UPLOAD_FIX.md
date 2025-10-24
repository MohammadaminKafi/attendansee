# Image Upload Fix - Backend Changes

## Summary
Fixed image upload functionality by converting the `original_image_path` field from CharField to ImageField and adding proper media file handling.

## Changes Made

### 1. Model Update
**File**: `backend/attendance/models.py`

Changed the `Image` model's `original_image_path` field:
```python
# Before
original_image_path = models.CharField(max_length=500)

# After  
original_image_path = models.ImageField(upload_to='session_images/', max_length=500)
```

This change:
- Enables proper file upload handling through Django forms/serializers
- Automatically validates file types
- Manages file storage location (uploads to `media/session_images/`)
- Returns the file URL through the API

### 2. Settings Update
**File**: `backend/attendansee_backend/settings.py`

Added media file configuration:
```python
# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

This configuration:
- `MEDIA_URL`: The URL prefix for serving uploaded files
- `MEDIA_ROOT`: The filesystem path where uploaded files are stored

### 3. URL Configuration
**File**: `backend/attendansee_backend/urls.py`

Added imports and media file serving:
```python
from django.conf import settings
from django.conf.urls.static import static

# At the end of file
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

This enables serving uploaded files in development mode.

## Migration Required

After these changes, you need to create and run a migration:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

The migration will:
- Alter the `original_image_path` column from VARCHAR to Django's ImageField
- Existing data may need manual migration if any exists

## Frontend Compatibility

The ImageSerializer will now return:
```json
{
  "id": 1,
  "original_image_path": "/media/session_images/image_name.jpg",
  "session": 5,
  ...
}
```

The frontend needs to construct the full URL:
```typescript
const fullUrl = `${API_BASE_URL.replace('/api', '')}${image.original_image_path}`;
```

## API Usage

### Upload Image (Frontend)
```typescript
const formData = new FormData();
formData.append('session', sessionId.toString());
formData.append('original_image_path', fileObject);  // File object from input

await api.post('/attendance/images/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

### Response
```json
{
  "id": 123,
  "session": 5,
  "session_name": "Session 1",
  "class_name": "Class A",
  "original_image_path": "/media/session_images/abc123.jpg",
  "processed_image_path": "",
  "upload_date": "2025-10-23T10:30:00Z",
  "is_processed": false,
  "processing_date": null,
  "created_at": "2025-10-23T10:30:00Z",
  "updated_at": "2025-10-23T10:30:00Z",
  "face_crop_count": 0
}
```

## Production Considerations

For production deployment:

1. **Use a proper file storage backend** (e.g., AWS S3, Azure Blob Storage)
2. **Don't serve media files through Django** - use nginx or a CDN
3. **Add file validation** - file size limits, type validation
4. **Consider using django-storages** for cloud storage

Example nginx configuration for production:
```nginx
location /media/ {
    alias /path/to/attendansee/backend/media/;
}
```

## Security Notes

1. File uploads are validated by Django's ImageField
2. Only authenticated users with proper permissions can upload
3. Uploads are scoped to user's own sessions (validated in serializer)
4. Consider adding file size limits in settings:
   ```python
   DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
   FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
   ```

## Testing

Test the upload functionality:
1. Create a session through the frontend
2. Navigate to session detail page
3. Click "Upload Images"
4. Select one or more image files
5. Verify images appear in the grid
6. Check that images are saved in `backend/media/session_images/`
