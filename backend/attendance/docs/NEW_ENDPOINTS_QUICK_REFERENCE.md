# New Endpoints - Quick Reference Guide

Quick reference for the four new API endpoints added to AttendanSee backend.

---

## 1. Bulk Upload Students

```bash
POST /api/attendance/classes/{id}/bulk-upload-students/
```

**Upload CSV/Excel file with student data**

```bash
curl -X POST \
  http://localhost:8000/api/attendance/classes/1/bulk-upload-students/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@students.csv" \
  -F "has_header=true"
```

**CSV Format:**
```csv
first_name,last_name,student_id
John,Doe,S001
Jane,Smith,S002
```

**Returns:** List of created students + skipped duplicates

---

## 2. Process Image

```bash
POST /api/attendance/images/{id}/process-image/
```

**Process image to extract face crops**

```bash
curl -X POST \
  http://localhost:8000/api/attendance/images/1/process-image/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "min_face_size": 20,
    "confidence_threshold": 0.5
  }'
```

**Returns:** Processing status (HTTP 202 Accepted)

**Status:** Stub - integrate with `/core/face/extractor.py`

---

## 3. Aggregate Session Crops

```bash
POST /api/attendance/sessions/{id}/aggregate-crops/
```

**Match face crops to students in session**

```bash
curl -X POST \
  http://localhost:8000/api/attendance/sessions/1/aggregate-crops/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "similarity_threshold": 0.7,
    "auto_assign": false
  }'
```

**Returns:** Aggregation statistics

**Status:** Stub - integrate with `/core/face/aggregator.py`

---

## 4. Aggregate Class

```bash
POST /api/attendance/classes/{id}/aggregate-class/
```

**Get unified attendance statistics for entire class**

```bash
curl -X POST \
  http://localhost:8000/api/attendance/classes/1/aggregate-class/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "include_unprocessed": false,
    "date_from": "2025-10-01",
    "date_to": "2025-10-31"
  }'
```

**Returns:** Per-student attendance summary

**Status:** Stub - integrate with `/core/face/aggregator.py`

---

## Testing

Run tests for new endpoints:

```bash
cd backend
pytest attendance/tests/test_new_endpoints.py -v
```

Run specific test class:

```bash
pytest attendance/tests/test_new_endpoints.py::TestBulkStudentUpload -v
pytest attendance/tests/test_new_endpoints.py::TestProcessImage -v
pytest attendance/tests/test_new_endpoints.py::TestAggregateCrops -v
pytest attendance/tests/test_new_endpoints.py::TestAggregateClass -v
```

---

## Integration TODOs

### 1. Image Processing (`views.py` line ~250)
```python
# TODO: Implement actual face detection and extraction here
# 1. Load the image from original_image_path
# 2. Run face detection using the core face module
# 3. Extract face crops for each detected face
# 4. Save crops to disk
# 5. Create FaceCrop objects with coordinates and paths
# 6. Mark image as processed
```

### 2. Session Aggregation (`views.py` line ~330)
```python
# TODO: Implement actual crop aggregation logic here
# 1. Load face embeddings from all crops in the session
# 2. Cluster similar faces together
# 3. Match clusters with known students in the class
# 4. Assign crops to students based on similarity threshold
# 5. Update FaceCrop records with student assignments
```

### 3. Class Aggregation (`views.py` line ~130)
```python
# TODO: Implement actual aggregation logic here
# 1. Load face embeddings from all sessions
# 2. Perform cross-session face matching
# 3. Generate unified attendance records
# 4. Calculate attendance patterns and statistics
```

---

## Files Modified

- `attendance/serializers.py` - Added 4 new serializers
- `attendance/views.py` - Added 4 new action methods
- `attendance/tests/test_new_endpoints.py` - Added 40 tests
- `pyproject.toml` - Added openpyxl dependency
- `attendance/docs/NEW_ENDPOINTS_SUMMARY.md` - Full documentation

---

## Security Notes

✅ All endpoints require authentication
✅ Permission checks for class ownership
✅ File upload validation (size, type, content)
✅ Input parameter validation
✅ SQL injection protection (Django ORM)
✅ Atomic database transactions

---

## Next Steps

1. Install dependencies: `uv sync` or `pip install openpyxl`
2. Run migrations: `python manage.py migrate` (no new migrations needed)
3. Run tests: `pytest attendance/tests/test_new_endpoints.py`
4. Integrate core face recognition logic
5. Test end-to-end workflow
