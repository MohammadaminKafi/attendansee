# Student Merge Feature Implementation

## Overview
This document describes the implementation of the student merge functionality, which allows professors to merge two student records into one. This is useful when a student has been accidentally created twice or needs to be consolidated due to name changes or data entry errors.

## Backend Implementation

### 1. Serializer (`attendance/serializers.py`)

Added `MergeStudentSerializer`:
- **Purpose**: Validates merge request data
- **Required Field**: `target_student_id` (integer)
- **Validations**:
  - Target student must exist
  - Source and target must be different students
  - Both students must belong to the same class
  - User must have permission to access both students

### 2. API Endpoint (`attendance/views.py`)

Added `merge` action to `StudentViewSet`:
- **Endpoint**: `POST /api/attendance/students/{id}/merge/`
- **Parameters**:
  - `{id}`: ID of the source student (will be deleted)
  - Request body: `{ "target_student_id": <number> }`
- **Process**:
  1. Validates both students exist and belong to same class
  2. Transfers all face crops from source to target student
  3. Deletes the source student
  4. Returns statistics about the merge
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Successfully merged students",
    "source_student": {
      "id": 123,
      "full_name": "John Doe",
      "student_id": "S001"
    },
    "target_student": { ... },
    "statistics": {
      "face_crops_transferred": 15,
      "target_crops_before_merge": 8,
      "target_crops_after_merge": 23
    }
  }
  ```

### 3. Tests (`attendance/tests/test_merge_students.py`)

Comprehensive test suite covering:
- ✅ Successful merge with face crop transfer
- ✅ Merge with no face crops
- ✅ Validation: Cannot merge student with itself
- ✅ Validation: Students must be in same class
- ✅ Validation: Target student must exist
- ✅ Validation: target_student_id is required
- ✅ Permission: Unauthenticated access denied
- ✅ Permission: Cannot merge other users' students
- ✅ Face crop attributes preserved during merge
- ✅ Both students having face crops
- ✅ Response includes proper student data
- ✅ Invalid target_student_id type handling

## Frontend Implementation

### 1. Types (`frontend/src/types/index.ts`)

Added interfaces:
```typescript
interface MergeStudentData {
  target_student_id: number;
}

interface MergeStudentResponse {
  status: string;
  message: string;
  source_student: { ... };
  target_student: Student;
  statistics: { ... };
}
```

### 2. API Service (`frontend/src/services/api.ts`)

Added method to `studentsAPI`:
```typescript
mergeStudents: async (
  sourceStudentId: number, 
  data: MergeStudentData
): Promise<MergeStudentResponse>
```

### 3. UI Components (`frontend/src/components/tabs/StudentsTab.tsx`)

#### Changes:
1. **Icon-based Actions**: Replaced text buttons with minimal icons
   - 👁️ View icon (Eye)
   - 🔀 Merge icon (GitMerge)
   - ✏️ Edit icon (Edit2)
   - 🗑️ Delete icon (Trash2)

2. **Merge Mode**:
   - Click merge icon to enter merge mode
   - Source student is highlighted in blue
   - Info banner shows which student is being merged
   - Click another student to select as merge target
   - Cancel button to exit merge mode

3. **Merge Confirmation Modal**:
   - Shows source student (will be deleted) in red
   - Shows target student (will be kept) in green
   - Displays warning about irreversible action
   - Explains face crop transfer process
   - Requires explicit confirmation

#### User Workflow:
1. Click merge icon (🔀) next to a student
2. System enters merge mode and highlights selected student
3. Click on target student to merge into
4. Review merge details in confirmation modal
5. Confirm merge or cancel
6. System transfers face crops and deletes source student

### 4. Session Icons Fix (`frontend/src/components/tabs/SessionsTab.tsx`)

- Removed `opacity-0 group-hover:opacity-100` classes
- Edit and delete icons now always visible
- Maintains hover effects for better UX

## Edge Cases Handled

### Backend:
1. **Same Student**: Prevents merging a student with itself
2. **Different Classes**: Prevents cross-class merging
3. **Non-existent Student**: Returns appropriate error
4. **Missing Parameters**: Validates required fields
5. **Permissions**: Ensures user owns the class
6. **Transaction Safety**: Uses atomic transactions for data integrity
7. **Cascade Prevention**: Face crops are transferred before deletion

### Frontend:
1. **Merge Mode State**: Clear visual indicators
2. **Cancel Capability**: Easy exit from merge mode
3. **Confirmation Required**: Prevents accidental merges
4. **Loading States**: Shows progress during merge
5. **Error Handling**: Displays error messages
6. **UI Feedback**: Success/error alerts
7. **Data Refresh**: Reloads student list after merge

## API Documentation

### Merge Students Endpoint

**POST** `/api/attendance/students/{id}/merge/`

**Authentication**: Required

**Path Parameters**:
- `id` (integer): ID of the source student to merge from

**Request Body**:
```json
{
  "target_student_id": 456
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "Successfully merged students",
  "source_student": {
    "id": 123,
    "full_name": "John Doe",
    "student_id": "S001"
  },
  "target_student": {
    "id": 456,
    "class_enrolled": 10,
    "class_name": "CS 101",
    "first_name": "Jane",
    "last_name": "Smith",
    "full_name": "Jane Smith",
    "student_id": "S002",
    "email": "jane@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "statistics": {
    "face_crops_transferred": 15,
    "target_crops_before_merge": 8,
    "target_crops_after_merge": 23
  }
}
```

**Error Responses**:

400 Bad Request - Cannot merge with itself:
```json
{
  "non_field_errors": ["Cannot merge a student with itself"]
}
```

400 Bad Request - Different classes:
```json
{
  "non_field_errors": ["Students must belong to the same class to be merged"]
}
```

400 Bad Request - Target doesn't exist:
```json
{
  "target_student_id": ["Student with ID 999 does not exist"]
}
```

401 Unauthorized - Not authenticated:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

404 Not Found - Source student not found or no permission:
```json
{
  "detail": "Not found."
}
```

500 Internal Server Error:
```json
{
  "error": "Failed to merge students",
  "details": "Error message here"
}
```

## Testing

### Running Backend Tests
```bash
cd backend
pytest attendance/tests/test_merge_students.py -v
```

### Expected Test Results
- 13 tests covering all edge cases
- All validations working correctly
- Face crop transfer verified
- Permission checks validated

## Security Considerations

1. **Authorization**: Only class owners can merge students
2. **Validation**: Strict validation prevents invalid operations
3. **Transaction Safety**: Atomic operations prevent partial merges
4. **Audit Trail**: Source student info preserved in response
5. **No Cross-Class Operations**: Students must be in same class

## Future Enhancements

Potential improvements for future iterations:

1. **Undo Functionality**: Store merge history for reversal
2. **Bulk Merge**: Merge multiple students at once
3. **Smart Suggestions**: AI-based duplicate detection
4. **Audit Log**: Persistent merge history in database
5. **Preview**: Show face crops before merging
6. **Confidence Scores**: Update confidence after merge
7. **Email Notifications**: Notify about merges if applicable

## Conclusion

The student merge feature provides a robust solution for consolidating duplicate student records. It includes comprehensive validation, proper error handling, and a user-friendly interface that prevents accidental data loss while maintaining data integrity.
