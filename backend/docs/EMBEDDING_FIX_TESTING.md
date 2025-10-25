# Testing the Embedding Double Free Fix

## Quick Start

### 1. Restart Backend Server

```bash
cd backend
docker-compose down
docker-compose up --build
```

Or if running directly:
```bash
python manage.py runserver
```

### 2. Test from Frontend

1. Open browser and navigate to your app
2. Go to Classes → Select a class → Select a session → Select an image
3. Click on any face crop to open detail page
4. Click "Generate Embedding" button
5. Select "FaceNet (128D)" model
6. Click "Generate"

**Expected Result:**
- ✅ Loading spinner appears
- ✅ Success message: "Successfully generated 128D embedding using facenet model"
- ✅ Backend server stays running (no crash)
- ✅ Page shows embedding model updated

**What NOT to see:**
- ❌ Backend crash
- ❌ "free(): double free detected in tcache 2" error
- ❌ Connection refused errors

### 3. Test Multiple Embeddings

Generate embeddings for 2-3 more crops:
- Second crop should be faster (~0.5-1 second vs 2-5 seconds)
- All should complete successfully
- Backend should remain stable

## Detailed Testing

### Test Case 1: First Embedding Generation

**Steps:**
1. Select a face crop that doesn't have an embedding yet
2. Click "Generate Embedding"
3. Choose FaceNet model
4. Click Generate

**Expected:**
- Takes 2-5 seconds (loading model)
- Logs show: "Loading Facenet model (first time may take a while)..."
- Success response received
- Crop detail shows "FaceNet (128D)" as embedding model

**Check Backend Logs:**
```bash
docker-compose logs -f backend | grep -E "Generating|Loading|Successfully"
```

Should see:
```
INFO: Generating embedding for crop X using facenet
INFO: Loading Facenet model (first time may take a while)...
INFO: Processing crop image at: /path/to/crop.jpg
DEBUG: Generating FaceNet embedding for: /path/to/crop.jpg
DEBUG: Successfully generated FaceNet embedding with dimension: 128
INFO: Successfully generated 128D embedding for crop X
```

### Test Case 2: Cached Model (2nd Embedding)

**Steps:**
1. Select a different face crop
2. Generate embedding with FaceNet again

**Expected:**
- Takes 0.3-1 second (model cached)
- No "Loading model" message in logs
- Success response
- Faster than first time

### Test Case 3: ArcFace Model

**Steps:**
1. Select another face crop
2. Generate embedding with ArcFace model

**Expected:**
- Takes 3-7 seconds (loading ArcFace for first time)
- Success response
- Shows "ArcFace (512D)" in crop details

### Test Case 4: Force Regenerate

**Steps:**
1. Select a crop that already has an embedding
2. Click "Generate Embedding"
3. Check "Force regenerate" checkbox
4. Click Generate

**Expected:**
- Warning about existing embedding shown
- Regeneration happens
- New embedding replaces old one
- Backend stays stable

### Test Case 5: Concurrent Requests

**Steps:**
1. Open 3 browser tabs
2. In each tab, navigate to different face crops
3. Click "Generate Embedding" in all tabs within 1 second
4. All tabs should use FaceNet

**Expected:**
- Requests process one at a time (serialized)
- Each tab shows loading spinner
- All complete successfully (may take 5-10 seconds total)
- No crashes or errors

### Test Case 6: Error Handling

**Steps:**
1. Use browser dev tools
2. Find a crop ID that doesn't exist
3. Make API call to generate embedding for non-existent crop

**Expected:**
- Proper error response (404)
- Backend doesn't crash
- Error logged but server continues

## Monitoring

### Watch Logs in Real-Time

```bash
docker-compose logs -f backend
```

### Check for Errors

```bash
docker-compose logs backend | grep -i "error\|warning\|exception\|free"
```

Should NOT see:
- "free(): double free detected in tcache 2"
- "Aborted (core dumped)"
- Server restart messages

### Monitor Memory Usage

```bash
docker stats backend
```

**Expected:**
- Memory increases on first embedding (model loading)
- Memory stabilizes after first embedding
- No continuous memory growth

**Example:**
```
CONTAINER   CPU %   MEM USAGE / LIMIT     MEM %
backend     10%     300MB / 2GB          15%      # Initial
backend     50%     600MB / 2GB          30%      # During first load
backend     5%      650MB / 2GB          32%      # After first (stable)
backend     10%     660MB / 2GB          33%      # During 2nd embedding
backend     5%      650MB / 2GB          32%      # After 2nd (stable)
```

### Check Server Status

```bash
docker-compose ps
```

**Expected output:**
```
NAME      COMMAND                  STATUS
backend   "python manage.py ru…"   Up 5 minutes
```

Status should always be "Up", not "Restarting" or "Exited"

## Troubleshooting

### Issue: Server Still Crashes

**Check:**
1. Did you rebuild Docker container?
   ```bash
   docker-compose up --build
   ```

2. Is the fix applied?
   ```bash
   docker-compose exec backend grep -A5 "CUDA_VISIBLE_DEVICES" /app/attendance/services/embedding_service.py
   ```
   Should show: `os.environ['CUDA_VISIBLE_DEVICES'] = '-1'`

3. Check TensorFlow version:
   ```bash
   docker-compose exec backend python -c "import tensorflow as tf; print(tf.__version__)"
   ```

**Try:**
- Clear Docker cache: `docker-compose down -v`
- Rebuild: `docker-compose build --no-cache`
- Restart: `docker-compose up`

### Issue: Embeddings Take Too Long

**Normal timing:**
- First FaceNet: 2-5 seconds ✅
- First ArcFace: 3-7 seconds ✅
- Subsequent: 0.3-1.5 seconds ✅

**If slower:**
- Check CPU usage: `docker stats backend`
- Check if container has enough resources
- Consider using FaceNet (faster than ArcFace)

### Issue: "File not found" Error

**Check:**
1. Is the crop image file actually on disk?
   ```bash
   docker-compose exec backend ls -la /app/media/face_crops/
   ```

2. Are media files mounted correctly?
   Check `docker-compose.yml` volume mounts

**Fix:**
- Verify volume mounts in docker-compose.yml
- Ensure media folder permissions are correct

### Issue: Backend Logs Show Warnings

**Common warnings (safe to ignore):**
- "Could not find cuda drivers on your machine" - Expected, we use CPU
- "This TensorFlow binary is optimized..." - Expected, just info
- "I tensorflow/core/platform/cpu_feature_guard.cc" - Expected, just info

**Warnings to investigate:**
- "Error generating embedding" - Check file exists
- "Memory" related warnings - Monitor with `docker stats`
- "Thread" related warnings - Check if lock is working

## Performance Benchmarks

### Expected Timings

| Operation | First Time | Cached |
|-----------|------------|--------|
| FaceNet | 2-5 sec | 0.3-1 sec |
| ArcFace | 3-7 sec | 0.5-1.5 sec |

### Concurrent Performance

| Scenario | Expected Time |
|----------|---------------|
| 1 embedding | 0.5-1 sec (cached) |
| 3 concurrent | 1.5-3 sec (serialized) |
| 10 concurrent | 5-10 sec (serialized) |

Note: Requests are processed one at a time for stability

## Success Checklist

After testing, verify:

- [ ] Single embedding generation works
- [ ] Multiple embeddings work
- [ ] Backend stays running (no crashes)
- [ ] No "double free" errors in logs
- [ ] Model caching works (2nd+ faster)
- [ ] Both FaceNet and ArcFace work
- [ ] Memory usage is stable
- [ ] Concurrent requests handled gracefully
- [ ] Error cases handled properly
- [ ] Frontend shows success messages

## Reporting Issues

If the fix doesn't work:

1. **Collect information:**
   ```bash
   # Save logs
   docker-compose logs backend > backend_logs.txt
   
   # Check versions
   docker-compose exec backend python -c "import tensorflow as tf; import deepface; print(f'TF: {tf.__version__}'); print(f'DeepFace: {deepface.__version__}')" > versions.txt
   
   # Check memory
   docker stats --no-stream backend > stats.txt
   ```

2. **Include in report:**
   - Description of what you did
   - Expected vs actual behavior
   - Log files (backend_logs.txt)
   - Version info (versions.txt)
   - Memory stats (stats.txt)
   - Screenshots of error messages

3. **Open an issue** with all collected information

## Next Steps After Success

Once embeddings work:

1. **Generate embeddings for all crops** in a session:
   - Use batch generation endpoint
   - Or process one by one

2. **Test face crop assignment**:
   - Assign crops to students using KNN
   - Verify similarity matching works

3. **Test clustering**:
   - Cluster session crops
   - Verify groups make sense

4. **Production considerations**:
   - Consider using Celery for background processing
   - Monitor memory usage over time
   - Set up proper logging/monitoring
   - Consider GPU server for better performance

---

**Last Updated**: October 25, 2025  
**Related Docs**: [EMBEDDING_DOUBLE_FREE_FIX.md](./EMBEDDING_DOUBLE_FREE_FIX.md)
