# New API Endpoints - Implementation Summary

This document provides an overview of the four new API endpoints that have been added to the AttendanSee backend.

## Overview

Four new endpoints have been implemented to support:
1. Bulk student upload from CSV/Excel files
2. Image processing to extract face crops
3. Session-level crop aggregation
4. Class-level attendance aggregation

All endpoints include proper authentication, authorization, validation, and comprehensive test coverage.

---

## 1. Bulk Student Upload

**Endpoint:** `POST /api/attendance/classes/{id}/bulk-upload-students/`

**Purpose:** Upload multiple students to a class from a CSV or Excel file.

### Request Format

- **Content-Type:** `multipart/form-data`
- **Required Parameters:**
  - `file`: CSV or Excel file (.csv, .xlsx, .xls)
- **Optional Parameters:**
  - `has_header`: Boolean indicating if file has header row (default: true)

### File Format

The file should contain at least 2 columns:
1. `first_name` (required)
2. `last_name` (required)
3. `student_id` (optional)

Example CSV:
```csv
first_name,last_name,student_id
John,Doe,S001
Jane,Smith,S002
Bob,Johnson,S003
```

### Response Format

```json
{
  "created": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "student_id": "S001",
      "class_enrolled": 1,
      "full_name": "John Doe",
      "created_at": "2025-10-23T12:00:00Z"
    }
  ],
  "total_created": 3,
  "total_skipped": 1,
  "skipped": [
    {
      "first_name": "Alice",
      "last_name": "Brown",
      "student_id": "S004",
      "reason": "Already exists"
    }
  ],
  "message": "Successfully created 3 students. Skipped 1 duplicates."
}
```

### Security Features

- **File Size Limit:** 5MB maximum
- **Student Limit:** 1000 students per upload
- **File Type Validation:** Only CSV and Excel files allowed
- **Content Validation:** Validates required fields, empty values, and data integrity
- **UTF-8 BOM Support:** Handles UTF-8 encoded files with BOM
- **Duplicate Detection:** Skips students that already exist in the class
- **Authorization:** Only class owner or admin can upload

### Error Handling

- Empty files
- Invalid file formats
- Missing required columns
- Empty first/last names
- File size exceeded
- Encoding errors
- Invalid class access

---

## 2. Process Image

**Endpoint:** `POST /api/attendance/images/{id}/process-image/`

**Purpose:** Process an image to extract face crops for attendance detection.

### Request Format

```json
{
  "min_face_size": 20,
  "confidence_threshold": 0.5
}
```

**Parameters (all optional):**
- `min_face_size`: Minimum face size in pixels (10-500, default: 20)
- `confidence_threshold`: Confidence threshold for detection (0.0-1.0, default: 0.5)

### Response Format

```json
{
  "status": "processing_queued",
  "image_id": 1,
  "session_id": 1,
  "class_id": 1,
  "parameters": {
    "min_face_size": 20,
    "confidence_threshold": 0.5
  },
  "faces_detected": 0,
  "crops_created": [],
  "message": "Image processing initiated. Note: Full processing logic will be implemented with core face recognition module."
}
```

### Implementation Status

**Current:** Stub implementation that validates input and returns processing status.

**To Be Implemented:**
1. Load image from `original_image_path`
2. Run face detection using core face module
3. Extract face crops for each detected face
4. Save crops to disk
5. Create `FaceCrop` objects with coordinates and paths
6. Mark image as processed with `mark_as_processed()`

### Validation

- Prevents reprocessing already processed images
- Validates parameter ranges
- Ensures user owns the class

---

## 3. Aggregate Session Crops

**Endpoint:** `POST /api/attendance/sessions/{id}/aggregate-crops/`

**Purpose:** Aggregate face crops from all images in a session and match them to students.

### Request Format

```json
{
  "similarity_threshold": 0.7,
  "auto_assign": false
}
```

**Parameters (all optional):**
- `similarity_threshold`: Threshold for face matching (0.0-1.0, default: 0.7)
- `auto_assign`: Automatically assign high-confidence matches (default: false)

### Response Format

```json
{
  "status": "aggregation_completed",
  "session_id": 1,
  "session_name": "Week 1 - Introduction",
  "class_id": 1,
  "parameters": {
    "similarity_threshold": 0.7,
    "auto_assign": false
  },
  "statistics": {
    "total_images": 5,
    "total_crops": 25,
    "identified_crops": 10,
    "unidentified_crops": 15,
    "identified_students": 8,
    "total_students_in_class": 20
  },
  "message": "Crop aggregation completed successfully. Note: Full aggregation logic will be implemented with core face recognition module."
}
```

### Implementation Status

**Current:** Stub implementation that validates input and returns statistics.

**To Be Implemented:**
1. Load face embeddings from all crops in the session
2. Cluster similar faces together
3. Match clusters with known students in the class
4. Assign crops to students based on similarity threshold
5. Update `FaceCrop` records with student assignments using `identify_student()`

### Validation

- Ensures session has images
- Checks that all images are processed before aggregation
- Validates parameter ranges
- Ensures user owns the class

---

## 4. Aggregate Class

**Endpoint:** `POST /api/attendance/classes/{id}/aggregate-class/`

**Purpose:** Aggregate attendance data across all sessions in a class for unified statistics.

### Request Format

```json
{
  "include_unprocessed": false,
  "date_from": "2025-10-01",
  "date_to": "2025-10-31"
}
```

**Parameters (all optional):**
- `include_unprocessed`: Include unprocessed sessions (default: false)
- `date_from`: Start date for aggregation (YYYY-MM-DD)
- `date_to`: End date for aggregation (YYYY-MM-DD)

### Response Format

```json
{
  "class_id": 1,
  "class_name": "Introduction to Computer Science",
  "total_sessions": 10,
  "total_students": 20,
  "date_range": {
    "from": "2025-10-01",
    "to": "2025-10-31"
  },
  "student_statistics": [
    {
      "student_id": 1,
      "name": "John Doe",
      "student_number": "S001",
      "total_sessions": 10,
      "attended_sessions": 8,
      "attendance_rate": 80.0,
      "total_detections": 15
    }
  ],
  "message": "Class aggregation completed successfully. Note: Full aggregation logic will be implemented with core face recognition module."
}
```

### Implementation Status

**Current:** Stub implementation that calculates basic statistics from existing data.

**To Be Implemented:**
1. Load face embeddings from all sessions
2. Perform cross-session face matching
3. Generate unified attendance records
4. Calculate attendance patterns and statistics
5. Identify trends and anomalies

### Validation

- Validates date range (date_from <= date_to)
- Filters sessions based on processing status and date range
- Ensures user owns the class

---

## Testing

Comprehensive test suite created in `attendance/tests/test_new_endpoints.py` covering:

### Bulk Upload Tests (18 tests)
- CSV and Excel file upload
- Files with/without headers
- Duplicate handling
- Empty file validation
- File size limits
- Invalid file formats
- Missing required columns
- Empty names validation
- Empty row skipping
- UTF-8 BOM support
- Authorization and permission checks

### Process Image Tests (6 tests)
- Successful processing
- Custom parameters
- Already processed image handling
- Invalid parameter validation
- Authorization and permission checks

### Aggregate Crops Tests (7 tests)
- Successful aggregation
- Custom parameters
- Sessions without images
- Unprocessed images handling
- Invalid threshold validation
- Authorization and permission checks

### Aggregate Class Tests (9 tests)
- Successful aggregation
- Date range filtering
- Including unprocessed sessions
- Invalid date range handling
- Empty class handling
- Student statistics calculation
- Authorization and permission checks

**Total Tests:** 40 comprehensive tests

---

## Security Considerations

1. **Authentication Required:** All endpoints require valid JWT token
2. **Authorization:** Users can only access their own classes/sessions/images
3. **Admin Override:** Admin users have access to all resources
4. **File Upload Security:**
   - File size limits (5MB)
   - File type validation
   - Content validation
   - Encoding validation
5. **Input Validation:** All parameters are validated with appropriate ranges
6. **Database Transactions:** Bulk operations use atomic transactions

---

## Dependencies Added

- `openpyxl>=3.1.5`: For Excel file parsing support

---

## URL Patterns

The following URL patterns are automatically created by Django REST Framework's router:

```
POST /api/attendance/classes/{id}/bulk-upload-students/
POST /api/attendance/classes/{id}/aggregate-class/
POST /api/attendance/images/{id}/process-image/
POST /api/attendance/sessions/{id}/aggregate-crops/
```

---

## Integration with Core Module

All endpoints are designed to be integrated with the core face recognition module located in `/core/face/`. The stub implementations provide clear TODO comments indicating where the actual processing logic should be added.

### Integration Points

1. **Image Processing:** Connect to `/core/face/extractor.py` for face detection and extraction
2. **Crop Aggregation:** Connect to `/core/face/aggregator.py` for face clustering and matching
3. **Class Aggregation:** Use aggregator for cross-session face matching

### Model Methods to Use

- `Image.mark_as_processed(processed_path)`: Mark image as processed
- `FaceCrop.identify_student(student, confidence)`: Assign student to crop
- `Session.update_processing_status()`: Update session status after processing

---

## Future Enhancements

1. **Async Processing:** Move image processing to background tasks (Celery)
2. **Progress Tracking:** Add WebSocket support for real-time progress updates
3. **Batch Processing:** Support processing multiple images at once
4. **Export Functionality:** Export aggregation results to PDF/Excel
5. **Advanced Filtering:** Add more sophisticated filtering options
6. **Caching:** Cache aggregation results for better performance

---

## Notes

- All stub implementations return appropriate HTTP status codes and informative messages
- The actual face recognition logic should be implemented by integrating with the core module
- All endpoints maintain backward compatibility with existing APIs
- Test coverage ensures endpoints work correctly before core integration
