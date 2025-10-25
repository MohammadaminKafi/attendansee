# Quick Start Guide: Image Processing & Face Crop Management

## For Professors/Users

### 1. Processing Images

#### Option A: Process All Images
1. Navigate to a session's page
2. Click the **"Process All"** button at the top of the images section
3. Wait for the progress bar to complete
4. All images will now show detected faces

#### Option B: Process Individual Images
1. Navigate to a session's page
2. Hover over an unprocessed image (yellow indicator)
3. Click the **"Process"** button that appears
4. Wait for processing to complete (green indicator appears)

### 2. Managing Face Crops

#### View Detected Faces
1. Click on any processed image
2. The Image Detail page shows:
   - Original image (left)
   - Processed image with face boxes (right)
   - Grid of detected face crops below

#### Assign Student to Face Crop
1. On the Image Detail page
2. Hover over an unidentified face crop (yellow badge)
3. Click **"Assign Student"**
4. Select a student from the list
5. Click **"Assign"**

#### Remove Student Assignment
1. Hover over an identified face crop (green badge)
2. Click **"Unassign"** button
3. The face crop returns to unidentified status

#### Edit Student Information
1. Hover over an identified face crop
2. Click **"Edit Info"**
3. Update first name, last name, or student ID
4. Click **"Save Changes"**

#### Delete Face Crop
1. Hover over any face crop
2. Click **"Delete"** (trash icon)
3. Confirm deletion
4. Face crop is permanently removed

### 3. Navigation

- **Back to Session**: Click the back arrow or breadcrumb
- **Back to Class**: Use breadcrumb navigation
- **To Image Detail**: Click any image thumbnail

## Keyboard Shortcuts (Future)

Currently navigation is mouse-based. Keyboard shortcuts planned for future release.

## Common Tasks

### Task: Process New Session Images
1. Upload all images to the session
2. Click "Process All" button
3. Wait for completion
4. Review detected faces by clicking on images

### Task: Identify All Students in Session
1. Process all images (if not done)
2. Click through each image
3. For each unidentified face:
   - Click "Assign Student"
   - Select correct student
   - Save
4. Continue until all faces are identified

### Task: Fix Wrong Identification
1. Navigate to the image with wrong identification
2. Hover over the face crop
3. Click "Unassign"
4. Click "Assign Student" again
5. Select correct student

### Task: Remove False Positives
1. Navigate to image with false positive
2. Hover over the incorrect face crop
3. Click "Delete"
4. Confirm deletion

## Tips & Best Practices

### Image Upload
- Take photos from multiple angles
- Ensure good lighting
- Avoid excessive blur
- Limit to 20 images per session

### Processing
- Process all images at once for efficiency
- Better internet connection = faster processing
- Don't navigate away during processing

### Face Identification
- Start with clear, frontal face images
- Verify student list is complete before identifying
- Use "Edit Info" to correct student details

### Data Management
- Regularly review identified faces
- Remove duplicate or poor quality face crops
- Keep student information up to date

## Troubleshooting

### Images Not Processing
- **Check internet connection**
- **Verify image format** (JPG, PNG)
- **Try processing individually** if batch fails
- **Check browser console** for errors

### No Faces Detected
- **Image quality**: Ensure faces are clear and well-lit
- **Face size**: Faces should be reasonably large in frame
- **Angle**: Frontal or near-frontal views work best
- **Try different image**: Some images may not detect faces

### Can't Assign Student
- **Verify student exists** in class roster
- **Check permissions**: Ensure you own the class
- **Refresh page**: Sometimes state gets out of sync
- **Contact admin**: If issues persist

### Processing Takes Too Long
- **Normal for many images**: Large batches take time
- **Sequential processing**: Images process one by one
- **Don't close browser**: Let it complete
- **Split into smaller batches**: Upload fewer images per session

### Face Crop Not Deleting
- **Check permissions**: Ensure you own the class
- **Refresh page**: Try again after refresh
- **Network issues**: Check internet connection

## Status Indicators

### Image Status
- 🟢 **Green dot**: Processed successfully
- 🟡 **Yellow dot (pulsing)**: Pending processing

### Face Crop Status
- ✅ **Green badge "Identified"**: Student assigned
- ⚠️ **Yellow badge "Unidentified"**: No student assigned

### Processing Status
- **Spinner animation**: Processing in progress
- **Progress bar**: Batch processing completion percentage
- **"Processing..." text**: Individual image being processed

## Error Messages

### Common Errors

**"Failed to process image"**
- Retry processing
- Check image file integrity
- Verify network connection

**"Failed to load image data"**
- Refresh the page
- Check URL parameters
- Verify image still exists

**"Maximum image limit reached"**
- Delete unused images
- Create new session for more images

**"No students available"**
- Add students to class first
- Refresh student list

**"Image has already been processed"**
- Navigate to image detail to view results
- No action needed

## Support

For additional help or to report issues:
1. Check browser console for errors
2. Take screenshot of problem
3. Note exact steps to reproduce
4. Contact system administrator

---

**Version**: 1.0  
**Last Updated**: October 2025  
**Author**: AttendanSee Development Team
