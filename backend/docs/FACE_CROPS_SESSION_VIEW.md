# Face Crops Session View Feature

## Overview
This document describes the implementation of the face crops management feature that allows viewing and managing all face crops from all images within a session, with sorting, filtering, and categorization capabilities.

## Features Implemented

### 1. Session-Level Face Crops View
- View all detected faces from all images in a session in one unified interface
- Toggle between grid view and grouped-by-student view
- Sort face crops by multiple criteria
- Perform all standard operations (assign, edit, delete, unassign)

### 2. Sorting Options
The following sorting options are available:
- **Identified First**: Show identified faces before unidentified ones
- **Unidentified First**: Show unidentified faces before identified ones
- **Name (A-Z)**: Sort by student name in ascending order
- **Name (Z-A)**: Sort by student name in descending order
- **Newest First**: Sort by creation date (most recent first)

### 3. View Modes
- **Grid View**: Display all face crops in a uniform grid layout
- **Grouped View**: Organize face crops by assigned student name

### 4. Operations
All face crop operations available in the image detail page are also available here:
- **Assign Student**: Assign a face crop to a student with searchable dropdown
- **Edit Student Info**: Update student information directly from the face crop
- **Unassign Student**: Remove student assignment from a face crop
- **Delete Face Crop**: Permanently remove a face crop

## Backend Implementation

### API Endpoint

**URL**: `GET /api/sessions/{session_id}/face-crops/`

**Query Parameters**:
- `is_identified` (optional): Filter by identification status (true/false)
- `student_id` (optional): Filter by specific student ID
- `sort` (optional): Sort order - 'name', 'identified', 'created' (default: 'created')

**Response**:
```json
{
  "session_id": 1,
  "session_name": "Session 1",
  "total_crops": 25,
  "identified_crops": 15,
  "unidentified_crops": 10,
  "face_crops": [
    {
      "id": 1,
      "image": 5,
      "student": 3,
      "student_name": "John Doe",
      "crop_image_path": "/media/face_crops/...",
      "is_identified": true,
      "session_id": 1,
      "session_name": "Session 1",
      "class_id": 1,
      "class_name": "Math 101",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Implementation Details

Located in `backend/attendance/views.py`:

```python
@action(detail=True, methods=['get'])
def face_crops(self, request, pk=None):
    """Get all face crops for all images in this session"""
    session = self.get_object()
    
    # Get all images for this session
    images = Image.objects.filter(session=session)
    
    # Get all face crops for these images
    queryset = FaceCrop.objects.filter(
        image__in=images
    ).select_related('student', 'image__session__class_obj')
    
    # Filter by identification status
    is_identified = request.query_params.get('is_identified')
    if is_identified is not None:
        is_identified_bool = is_identified.lower() == 'true'
        queryset = queryset.filter(is_identified=is_identified_bool)
    
    # Filter by student
    student_id = request.query_params.get('student_id')
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    
    # Sort
    sort = request.query_params.get('sort', 'created')
    if sort == 'name':
        queryset = queryset.annotate(
            student_name_lower=Case(
                When(student__isnull=False, 
                     then=Lower(Concat('student__first_name', Value(' '), 'student__last_name'))),
                default=Value('zzz'),
                output_field=CharField()
            )
        ).order_by('student_name_lower')
    elif sort == 'identified':
        queryset = queryset.order_by('-is_identified', 'id')
    else:  # default to 'created'
        queryset = queryset.order_by('-created_at')
    
    # Serialize the data
    serializer = FaceCropDetailSerializer(queryset, many=True)
    
    # Calculate statistics
    total_crops = queryset.count()
    identified_crops = queryset.filter(is_identified=True).count()
    
    return Response({
        'session_id': session.id,
        'session_name': session.name,
        'total_crops': total_crops,
        'identified_crops': identified_crops,
        'unidentified_crops': total_crops - identified_crops,
        'face_crops': serializer.data
    })
```

### Key Implementation Notes

1. **Null Handling in Sorting**: Uses Django's `Case/When/Value` to handle null student names by assigning them 'zzz' to push them to the end
2. **Efficient Queries**: Uses `select_related()` to optimize database queries
3. **Flexible Filtering**: Supports multiple filter combinations
4. **Statistics**: Returns aggregate statistics alongside the data

## Frontend Implementation

### Components

#### 1. FaceCropsSection Component
**Location**: `frontend/src/components/ui/FaceCropsSection.tsx`

Reusable component for displaying and managing face crops with full CRUD operations.

**Props**:
```typescript
interface FaceCropsSectionProps {
  faceCrops: FaceCropDetail[];
  students: Student[];
  onUpdate: () => Promise<void>;
  title?: string;
  description?: string;
  showImageInfo?: boolean;
}
```

**Features**:
- Grid and grouped view modes with toggle
- Sorting dropdown (5 options)
- Assign student modal with search
- Edit student info modal
- Delete confirmation modal
- Unassign student action
- Responsive grid layout

**State Management**:
- View mode state (grid/grouped)
- Sort option state
- Modal states for each operation
- Search query for student assignment

#### 2. SessionDetailPage Integration
**Location**: `frontend/src/pages/SessionDetailPage.tsx`

**Added State**:
```typescript
const [faceCrops, setFaceCrops] = useState<FaceCropDetail[]>([]);
const [students, setStudents] = useState<Student[]>([]);
const [showFaceCropsSection, setShowFaceCropsSection] = useState(false);
```

**Data Loading**:
```typescript
const loadData = async () => {
  const [sessionData, classInfo, imagesData, studentsData, faceCropsResponse] = 
    await Promise.all([
      sessionsAPI.getSession(parseInt(sessionId)),
      classesAPI.getClass(parseInt(classId)),
      imagesAPI.getImages(parseInt(sessionId)),
      studentsAPI.getStudents(parseInt(classId)),
      sessionsAPI.getSessionFaceCrops(parseInt(sessionId))
    ]);
  
  setFaceCrops(faceCropsResponse.face_crops);
  
  // Show section if there are crops
  if (faceCropsResponse.face_crops.length > 0) {
    setShowFaceCropsSection(true);
  }
};
```

**Update Callback**:
```typescript
const handleFaceCropsUpdate = async () => {
  const faceCropsResponse = await sessionsAPI.getSessionFaceCrops(parseInt(sessionId));
  setFaceCrops(faceCropsResponse.face_crops);
  
  // Also reload images to update face crop counts
  const imagesData = await imagesAPI.getImages(parseInt(sessionId));
  setImages(imagesData);
};
```

**Rendering**:
```tsx
{showFaceCropsSection && (
  <Card className="mt-6">
    <FaceCropsSection
      faceCrops={faceCrops}
      students={students}
      onUpdate={handleFaceCropsUpdate}
      title="Session Face Crops"
      description={`All detected faces across ${images.length} image${images.length !== 1 ? 's' : ''}`}
      showImageInfo={true}
    />
  </Card>
)}
```

#### 3. ImageDetailPage Sorting Enhancement
**Location**: `frontend/src/pages/ImageDetailPage.tsx`

**Added State**:
```typescript
const [sortOption, setSortOption] = useState<
  'identified-first' | 'unidentified-first' | 'name-asc' | 'name-desc' | 'created-desc'
>('identified-first');
```

**Sorting Function**:
```typescript
const sortFaceCrops = (crops: FaceCropDetail[]) => {
  const sorted = [...crops];
  
  switch (sortOption) {
    case 'identified-first':
      return sorted.sort((a, b) => {
        if (a.is_identified === b.is_identified) return 0;
        return a.is_identified ? -1 : 1;
      });
    case 'unidentified-first':
      return sorted.sort((a, b) => {
        if (a.is_identified === b.is_identified) return 0;
        return a.is_identified ? 1 : -1;
      });
    case 'name-asc':
      return sorted.sort((a, b) => {
        const nameA = a.student_name || 'zzz';
        const nameB = b.student_name || 'zzz';
        return nameA.localeCompare(nameB);
      });
    case 'name-desc':
      return sorted.sort((a, b) => {
        const nameA = a.student_name || 'zzz';
        const nameB = b.student_name || 'zzz';
        return nameB.localeCompare(nameA);
      });
    case 'created-desc':
      return sorted.sort((a, b) => {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
    default:
      return sorted;
  }
};
```

**UI Addition**:
```tsx
{faceCrops.length > 0 && (
  <div className="flex items-center gap-2">
    <label className="text-sm text-gray-400">Sort by:</label>
    <select
      value={sortOption}
      onChange={(e) => setSortOption(e.target.value as any)}
      className="bg-dark-bg border border-dark-border rounded px-3 py-1.5 text-sm text-white"
    >
      <option value="identified-first">Identified First</option>
      <option value="unidentified-first">Unidentified First</option>
      <option value="name-asc">Name (A-Z)</option>
      <option value="name-desc">Name (Z-A)</option>
      <option value="created-desc">Newest First</option>
    </select>
  </div>
)}
```

### API Integration

**Location**: `frontend/src/services/api.ts`

**New Method**:
```typescript
export const sessionsAPI = {
  // ... existing methods ...
  
  getSessionFaceCrops: async (
    sessionId: number,
    params?: {
      is_identified?: boolean;
      student_id?: number;
      sort?: 'name' | 'identified' | 'created';
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.is_identified !== undefined) {
      queryParams.append('is_identified', String(params.is_identified));
    }
    if (params?.student_id) {
      queryParams.append('student_id', String(params.student_id));
    }
    if (params?.sort) {
      queryParams.append('sort', params.sort);
    }
    
    const url = `/sessions/${sessionId}/face-crops/${
      queryParams.toString() ? `?${queryParams.toString()}` : ''
    }`;
    
    const response = await apiClient.get(url);
    return response.data;
  },
};
```

## User Workflow

### Viewing Session Face Crops

1. Navigate to a session detail page
2. Upload and process images (if not already done)
3. Scroll down to see the "Session Face Crops" section
4. Choose between grid view and grouped view using the toggle
5. Select a sorting option from the dropdown

### Managing Face Crops

#### Assigning a Student
1. Hover over an unidentified face crop
2. Click "Assign Student"
3. Search for the student in the modal
4. Select the student
5. Click "Assign"

#### Editing Student Information
1. Hover over an identified face crop
2. Click "Edit Info"
3. Update first name, last name, or student ID
4. Click "Save Changes"

#### Unassigning a Student
1. Hover over an identified face crop
2. Click "Unassign"
3. The face crop becomes unidentified

#### Deleting a Face Crop
1. Hover over any face crop
2. Click "Delete"
3. Confirm deletion in the modal
4. The face crop is permanently removed

### Grouped View

In grouped view mode:
- Face crops are organized by student name
- Unidentified faces appear in a separate "Unidentified Faces" section
- Each student group shows the student's full name and the number of crops
- Collapse/expand functionality for each group

## Technical Considerations

### Performance
- Uses `select_related()` for efficient database queries
- Parallel loading of data on page load (`Promise.all()`)
- Optimized re-rendering with React hooks

### Data Consistency
- After any update operation, both face crops and images are reloaded
- This ensures face crop counts on images are always accurate
- Updates propagate across all views automatically

### Error Handling
- All API calls wrapped in try-catch blocks
- User-friendly error messages displayed
- Failed operations don't break the UI

### Responsiveness
- Grid adapts to screen size (2-5 columns)
- Modals work well on mobile devices
- Touch-friendly action buttons

## Future Enhancements

Potential improvements to consider:
1. Bulk operations (assign/delete multiple crops at once)
2. Filtering UI in the frontend (currently only via API)
3. Drag-and-drop to assign students
4. Face similarity grouping suggestions
5. Export face crops as a report
6. Keyboard shortcuts for common operations
7. Infinite scroll for large datasets

## Testing Checklist

- [ ] Load session page with no images
- [ ] Upload and process multiple images
- [ ] Verify face crops appear in session view
- [ ] Test grid view display
- [ ] Test grouped view display
- [ ] Test all 5 sorting options
- [ ] Assign student from session view
- [ ] Edit student info from session view
- [ ] Unassign student from session view
- [ ] Delete face crop from session view
- [ ] Verify changes reflect in image detail page
- [ ] Test sorting in image detail page
- [ ] Test with large number of crops (20+ images)
- [ ] Test responsive behavior on mobile
- [ ] Test error handling (network errors, invalid data)

## Related Documentation

- [Face Detection Implementation](./FACE_DETECTION_IMPLEMENTATION.md)
- [Image Fields Fix](./IMAGE_FIELDS_COMPLETE_FIX.md)
- [Student Merge Feature](./STUDENT_MERGE_FEATURE.md)
