# Session Image Management - User Guide

## Overview
The Session Detail page allows you to upload, view, and manage images for attendance sessions. Each session can have up to 20 images that will be processed for face detection and attendance tracking.

## Accessing the Session Detail Page

### Method 1: Click Session Row
1. Navigate to a class from the Classes page
2. Click on the "Sessions" tab
3. Click anywhere on a session row in the table
4. You'll be redirected to the Session Detail page

### Method 2: Direct URL
Navigate to: `/classes/{classId}/sessions/{sessionId}`

## Page Overview

When you open a session, you'll see:
- **Breadcrumb navigation** at the top (Classes > Class Name > Session Name)
- **Session information card** with date, times, notes, and status
- **Statistics dashboard** showing:
  - Number of images uploaded
  - Total faces detected
  - Number of identified faces
- **Images section** for uploading and managing images

## Uploading Images

### How to Upload
1. Click the **"Upload Images"** button
2. Select one or multiple image files from your computer
3. Wait for the upload to complete
4. Images will appear in the grid immediately after upload

### Upload Limits
- **Maximum**: 20 images per session
- **File types**: Common image formats (JPG, PNG, etc.)
- **Multiple files**: You can select and upload multiple images at once
- **Remaining slots**: The page shows "X / 20 images uploaded"

### Upload Behavior
- If you try to upload more than the remaining slots, only the first N files will be uploaded
- Example: If 18 images exist and you select 5 files, only 2 will be uploaded
- You'll see a warning message if the limit is reached

## Viewing Images

### Image Grid Layout
- Images are displayed in a responsive grid
- **Mobile**: 2 columns
- **Tablet**: 3-4 columns  
- **Desktop**: 4-5 columns

### Image Information (Hover)
Hover over any image to see:
- **Processing status**: Green checkmark (Processed) or Yellow X (Pending)
- **Upload date and time**: When the image was added
- **Face count**: Number of faces detected in the image
- **Delete button**: Red trash icon to remove the image

### Status Indicators
Each image has a small colored dot in the top-right corner:
- 🟢 **Green dot**: Image has been processed
- 🟡 **Yellow dot** (pulsing): Processing pending

## Deleting Images

### How to Delete
1. Hover over the image you want to remove
2. Click the **red trash icon** button that appears
3. Confirm the deletion in the popup dialog
4. The image will be removed from the grid immediately

### Delete Confirmation
- A confirmation dialog prevents accidental deletions
- Click "OK" to confirm or "Cancel" to abort

⚠️ **Warning**: Deleted images cannot be recovered!

## Image Processing

### What is Processing?
After uploading, the system analyzes each image to:
1. Detect faces in the image
2. Match faces to enrolled students
3. Mark attendance for identified students

### Processing Status
- **Pending**: Image uploaded but not yet analyzed (yellow status)
- **Processed**: Face detection completed (green status)

### Processing Time
- Processing happens automatically after upload
- Time varies based on image size and number of faces
- Refresh the page to see updated processing status

## Statistics

The statistics cards show real-time counts:

### Images Card
- Total number of images uploaded to this session
- Updates immediately when you upload or delete images

### Total Faces Card
- Combined count of all faces detected across all images
- Updates after images are processed

### Identified Card
- Number of faces that were matched to enrolled students
- Updates after processing completes

## Tips & Best Practices

### Image Quality
✅ **Do:**
- Use clear, well-lit photos
- Ensure faces are visible and unobstructed
- Use recent photos for better matching
- Take photos from a similar angle

❌ **Don't:**
- Upload blurry or dark images
- Use images with faces partially hidden
- Upload duplicate images
- Use photos with extreme angles

### Optimal Session Setup
1. **Before class**: Create the session and add basic info
2. **During class**: Take photos with a phone or camera
3. **After class**: Upload all photos at once
4. **Review**: Check processing status and face counts
5. **Verify**: Review identified students for accuracy

### Batch Operations
- Upload multiple images simultaneously to save time
- The system processes uploads sequentially
- You can delete and re-upload if needed

### Managing Large Sessions
- For classes with many students, take multiple photos
- Different angles capture more faces
- Use the 20-image limit wisely - quality over quantity
- One or two good group photos may be better than many poor individual shots

## Navigation

### Breadcrumb Navigation
Click any item in the breadcrumb to navigate:
- **Classes**: Return to classes list
- **Class Name**: Return to class detail page
- **Session Name**: Current page (not clickable)

### Back to Sessions
Click "Classes" → Class Name → "Sessions" tab to return to the sessions list

## Troubleshooting

### Problem: Upload button is disabled
**Cause**: You've reached the 20-image limit  
**Solution**: Delete some images to free up slots

### Problem: Images not appearing
**Cause**: Upload may have failed  
**Solution**: Check for error messages and try uploading again

### Problem: Processing status not updating
**Cause**: Page doesn't auto-refresh  
**Solution**: Refresh the browser page to see latest status

### Problem: Can't delete image
**Cause**: May be a permission or network issue  
**Solution**: Refresh the page and try again, check your connection

### Problem: Wrong images uploaded
**Cause**: Selected wrong files  
**Solution**: Delete the incorrect images and upload the correct ones

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Upload images | Click Upload button (no keyboard shortcut yet) |
| Navigate back | Click breadcrumb or use browser back button |
| Confirm delete | Enter key in confirmation dialog |
| Cancel delete | Esc key in confirmation dialog |

## Mobile Usage

### Touch Interactions
- **Tap image**: Shows overlay with details
- **Tap delete button**: Confirms and deletes
- **Tap upload**: Opens file picker

### Mobile Tips
- Grid shows 2 columns for better visibility
- Swipe up/down to scroll through images
- Use camera icon in file picker to take photos directly

## Session Status

The session card shows overall processing status:
- **Processed**: All images have been analyzed
- **Pending**: Some images still need processing

This status is separate from individual image processing status.

## Data Privacy & Security

- Images are stored securely on the server
- Only class owners and admins can view session images
- Deleted images are permanently removed
- Face data is used only for attendance tracking

## Related Features

- **Sessions Tab**: Create, edit, and manage sessions
- **Students Tab**: View students and their attendance records
- **Class Dashboard**: Overview of class statistics
- **CSV Export**: Download attendance reports

## Need Help?

If you encounter issues:
1. Check this guide for solutions
2. Refresh the page to resolve temporary issues
3. Verify your internet connection
4. Contact system administrator for persistent problems
