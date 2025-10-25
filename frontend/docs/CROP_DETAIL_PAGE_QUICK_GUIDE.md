# Face Crop Detail Page - Quick Guide

## Accessing the Page

**Path:** `/classes/:classId/sessions/:sessionId/images/:imageId/crops/:cropId`

**Navigation:** 
- Go to any Image Detail page
- Click on any face crop card
- You'll be redirected to the Face Crop Detail page

## Page Layout

### Left Column: Face Crop Display
- Large view of the face crop
- Status badge (Identified/Unidentified)
- Student name (if identified)

### Right Column: Details
- **Crop ID**: Unique identifier
- **Assigned Student**: Student name and confidence score
- **Source Image**: Link to view the original image
- **Coordinates**: Position in original image (x, y, width, height)
- **Embedding Model**: Which model was used (FaceNet/ArcFace)
- **Created**: Timestamp

### Bottom: Action Buttons
- **Generate Embedding**: Create face embedding vector
- **Assign to Student**: Auto-assign using KNN

## Generate Embedding

### When to Use
- When the crop doesn't have an embedding yet
- When you want to change the embedding model
- Before using automatic assignment

### Steps
1. Click **"Generate Embedding"**
2. Select model:
   - **FaceNet (128D)**: Fast, efficient, good for most cases
   - **ArcFace (512D)**: More accurate, better for large classes
3. If crop already has embedding, check "Force regenerate" to replace it
4. Click **"Generate"**
5. Wait for processing (usually 1-3 seconds)
6. See success message with dimension info

### Tips
- Use FaceNet for most scenarios (faster)
- Use ArcFace when you need higher accuracy
- All crops in a class should use the same model for best results

## Assign to Student

### Prerequisites
- The crop must have an embedding generated
- There must be labeled crops in the class (for KNN to work)

### Steps
1. Click **"Assign to Student"**
2. Configure parameters:
   - **K Value**: Number of neighbors to consider (default: 5)
     - Lower K = More precise but sensitive to outliers
     - Higher K = More stable but may dilute accuracy
   - **Similarity Threshold**: Minimum score to accept (default: 0.6)
     - Higher = More strict, fewer false positives
     - Lower = More lenient, may include uncertain matches
   - **Embedding Model**: Choose FaceNet or ArcFace
     - Must match the model used in labeled crops
   - **Use Voting**: Enable majority voting (recommended)
3. Click **"Assign"**
4. Wait for processing (usually 1-2 seconds)
5. Review result:
   - **Success**: Student name and confidence score
   - **No Match**: Error message if no suitable match found

### Understanding Results

#### Success
```
Successfully assigned crop to John Doe (confidence: 82.5%)
```
- The crop is now labeled with the student
- Confidence indicates how certain the match is
- You can review the assignment in the Image Detail page

#### No Match
```
Could not find a suitable match for this crop
```
Possible reasons:
- No labeled crops exist in the class yet
- All matches below similarity threshold
- The person is not in the student list
- The embedding quality is poor

### Troubleshooting

#### "This crop doesn't have an embedding yet"
- **Solution**: Click "Generate Embedding" first

#### "No suitable match found"
- **Try**: Lower the similarity threshold (e.g., 0.5 instead of 0.6)
- **Try**: Increase K value (e.g., 7 or 10)
- **Check**: Are there labeled crops in the class?
- **Consider**: Manual assignment from Image Detail page

#### "Assigned to wrong student"
- Go back to Image Detail page
- Use "Unassign" button in the crop's action menu
- Manually assign to correct student
- Or try assignment again with different parameters

## Best Practices

### For Embedding Generation
1. **Choose one model per class** - Don't mix FaceNet and ArcFace
2. **Generate embeddings in batch** - Process all crops before assigning
3. **Use ArcFace for accuracy** - If you have good hardware and large classes
4. **Use FaceNet for speed** - If you have limited resources or small classes

### For Assignment
1. **Start with defaults** (K=5, threshold=0.6, voting=true)
2. **Label some crops manually first** - At least 3-5 per student
3. **Review assignments** - Check confidence scores
4. **Adjust threshold based on results**:
   - Too many wrong assignments? → Increase threshold
   - Too few assignments? → Decrease threshold
5. **Use same embedding model** - As used in labeled crops

### Workflow Recommendation
1. Upload images to session
2. Process all images (detect faces)
3. **Generate embeddings for all crops** (choose model)
4. **Manually label 3-5 crops per student**
5. **Use batch assignment** on session or class level
6. **Review outliers** using crop detail page
7. **Fine-tune using individual assignment** with adjusted parameters

## Keyboard Shortcuts

- **Back to Image**: Click back button or browser back
- **Modal Cancel**: Press Escape key
- **Navigate**: Use breadcrumb navigation

## Navigation

**Breadcrumb Path:**
```
Classes → [Class Name] → [Session Name] → Image Details → Face Crop Details
```

**Back Button:**
- Returns to Image Detail page
- Maintains context (class, session, image)

## Related Pages

- **Image Detail Page**: View all crops in an image
- **Session Detail Page**: Batch operations on all session crops
- **Class Detail Page**: Class-wide crop management
- **Student Detail Page**: View all crops of a specific student

## Common Workflows

### New Crop Identification
1. Navigate to crop detail page
2. Generate embedding (FaceNet or ArcFace)
3. Try automatic assignment
4. If successful, done! If not, go to Image page for manual assignment

### Update Wrong Assignment
1. Go to Image Detail page
2. Find the crop
3. Use "Unassign" in hover menu
4. Navigate to crop detail
5. Try assignment with different parameters
6. Or manually assign from Image page

### Check Embedding Status
1. Navigate to crop detail page
2. Look at "Embedding Model" field
3. If "Not generated", generate one
4. If different model needed, regenerate with force option

### Quality Check
1. Review crop image (is face clearly visible?)
2. Check coordinates (reasonable position and size?)
3. Try embedding generation
4. Test assignment with different thresholds
5. Compare with similar crops manually

## API Endpoints Used

- `GET /api/attendance/face-crops/{id}/` - Load crop data
- `POST /api/attendance/face-crops/{id}/generate-embedding/` - Generate embedding
- `POST /api/attendance/face-crops/{id}/assign/` - Assign crop
- `GET /api/attendance/students/?class_id={classId}` - Get class students

## Notes

- All operations are non-destructive (except delete)
- You can regenerate embeddings safely
- Assignment can be undone from Image page
- Confidence scores help validate assignments
- Use crop detail page for fine-tuning, batch operations for efficiency
