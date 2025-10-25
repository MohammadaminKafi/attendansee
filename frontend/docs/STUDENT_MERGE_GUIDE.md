# Student Merge Feature - Frontend Guide

## Overview
The student merge feature allows users to consolidate two student records by transferring all face crops from one student to another and then deleting the source student.

## UI Location
**Path**: Classes → Class Detail → Students Tab

## User Flow

### Step 1: Initiate Merge
1. Navigate to the Students tab in a class
2. Locate the student you want to merge FROM (source)
3. Click the merge icon (🔀) next to the student's name

### Step 2: Select Target
1. The interface enters "Merge Mode"
2. A blue banner appears showing the source student
3. The source student card is highlighted
4. Click on the student you want to merge INTO (target)

### Step 3: Confirm Merge
1. A confirmation modal appears showing:
   - Source student (highlighted in red, will be deleted)
   - Target student (highlighted in green, will be kept)
   - Warning about irreversible action
   - Description of what will happen
2. Review the information carefully
3. Click "Merge Students" to confirm or "Cancel" to abort

### Step 4: Result
- Success message shows merge completed
- Student list refreshes automatically
- Source student is removed from the list
- Target student now has all face crops

## Canceling a Merge

You can cancel a merge at any time before confirmation:
- Click the "Cancel Merge" button in the header
- Click the X icon in the blue banner
- Click "Cancel" in the confirmation modal

## Visual Indicators

### Normal Mode
- Students displayed in cards with icons:
  - 👁️ View student details
  - 🔀 Start merge
  - ✏️ Edit student info
  - 🗑️ Delete student

### Merge Mode
- Blue banner at top with source student name
- Source student card has blue border
- Other students have hover effect (green border)
- Icons hidden during merge mode
- Cancel merge button in header

### Confirmation Modal
- ⚠️ Warning icon and message
- Source student in red box
- Downward arrow
- Target student in green box
- Detailed explanation of merge

## Important Notes

1. **Irreversible**: Once merged, the source student cannot be recovered
2. **Same Class Only**: Can only merge students within the same class
3. **Face Crops**: All face detection data is transferred
4. **No Self-Merge**: Cannot merge a student with themselves
5. **Permissions**: Must be the class owner to merge students

## Icon Changes

All student action buttons have been updated to icons:
- **View**: Eye icon (👁️)
- **Merge**: Git merge icon (🔀)
- **Edit**: Pencil icon (✏️)
- **Delete**: Trash icon (🗑️)

All icons are always visible (not just on hover) for better accessibility.

## Keyboard Shortcuts

Currently none, but future enhancements may include:
- `Escape` to cancel merge mode
- `Enter` to confirm merge

## Error Handling

Common errors and their meanings:

- **"Cannot merge a student with itself"**: You selected the same student as both source and target
- **"Students must belong to the same class"**: Internal error, shouldn't happen in UI
- **"Student does not exist"**: The target student was deleted during the merge process
- **"Authentication credentials were not provided"**: Session expired, please log in again
- **"Not found"**: You don't have permission to access this student

## Best Practices

1. **Double Check**: Always verify you're merging the correct students
2. **Review Face Crops**: Check both students' face crops before merging if possible
3. **Student IDs**: Note the student IDs before merging for reference
4. **Backup**: Export student list before bulk merge operations

## Troubleshooting

### Merge button not visible
- Ensure you're on the Students tab
- Check you're logged in as the class owner

### Cannot click on target student
- Make sure you've clicked the merge icon first
- Verify you're not clicking the same student
- Check the student is in the same class

### Merge fails with error
- Check your internet connection
- Verify both students still exist
- Ensure your session hasn't expired
- Contact support if error persists

## Related Features

- **Student Detail View**: View all face crops for a student before merging
- **Bulk Upload**: Import students from CSV (check for duplicates first)
- **Delete Student**: Alternative to merging if student has no face crops

## API Endpoint Used

`POST /api/attendance/students/{id}/merge/`

Request:
```json
{
  "target_student_id": 456
}
```

See backend API documentation for full details.
