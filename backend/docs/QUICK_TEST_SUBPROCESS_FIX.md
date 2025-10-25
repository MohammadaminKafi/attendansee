# Quick Test: Subprocess Embedding Fix

## Prerequisites

Make sure you've restarted the backend:
```bash
cd backend
docker-compose down
docker-compose up --build
```

## Test 1: Basic Embedding Generation (2 minutes)

### Steps:
1. Open your app in browser
2. Navigate: Classes → Pick any class → Pick any session → Pick any image
3. Click on a face crop thumbnail
4. Click "Generate Embedding" button
5. Select "FaceNet (128D)"
6. Click "Generate"

### Expected Result:
- ⏱️ Takes 3-7 seconds
- ✅ Success message appears: "Successfully generated 128D embedding using facenet model"
- ✅ Page shows "FaceNet (128D)" as embedding model
- ✅ **Backend does NOT crash**

### Check Backend Logs:
```bash
docker-compose logs backend | tail -20
```

Should see:
```
INFO: Generating FaceNet embedding for: /app/media/face_crops/...
DEBUG: Using subprocess isolation for FaceNet
DEBUG: Running embedding generation in subprocess
INFO: Successfully generated 128D FaceNet embedding
```

Should NOT see:
```
free(): double free detected in tcache 2  ❌
```

## Test 2: Multiple Embeddings (5 minutes)

Generate embeddings for 3 more crops (repeat Test 1 steps for different crops).

### Expected Result:
- ✅ All 4 embeddings generate successfully
- ✅ Each takes 3-7 seconds
- ✅ Backend remains running throughout
- ✅ No crashes or errors

## Test 3: Backend Stability Check (30 seconds)

### Check if server is still running:
```bash
docker-compose ps
```

Expected output:
```
NAME      STATUS
backend   Up X minutes  ✅
```

NOT:
```
backend   Restarting  ❌
backend   Exited      ❌
```

### Check memory usage:
```bash
docker stats --no-stream backend
```

Should show stable memory (not continuously growing).

## Test 4: Error in Logs Check (1 minute)

```bash
docker-compose logs backend | grep -i "free\|double\|abort\|crash"
```

**Expected**: No results (empty output) ✅

**If you see "free(): double free"**: Fix didn't work ❌

## Success Checklist

- [ ] Embedding generation works from frontend
- [ ] Backend stays running (doesn't crash)
- [ ] No "double free" errors in logs
- [ ] Multiple embeddings all succeed
- [ ] `docker-compose ps` shows backend "Up"

## If It Fails

### Still getting double free error?

1. **Verify code was updated:**
   ```bash
   docker-compose exec backend grep "USE_SUBPROCESS" /app/attendance/services/embedding_service.py
   ```
   Should show: `USE_SUBPROCESS = True`

2. **Try rebuilding without cache:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Check Python version in container:**
   ```bash
   docker-compose exec backend python --version
   ```
   Should be Python 3.13 or higher.

4. **Test subprocess manually:**
   ```bash
   docker-compose exec backend python -c "
   import subprocess
   import sys
   result = subprocess.run([sys.executable, '-c', 'print(\"test\")'], capture_output=True)
   print(result.stdout.decode())
   "
   ```
   Should print "test".

### Subprocess times out?

Edit `embedding_service.py` and increase timeout:
```python
# Line ~119
stdout, stderr = process.communicate(timeout=120)  # Increased to 120 seconds
```

### Other errors?

1. Collect logs:
   ```bash
   docker-compose logs backend > backend_logs.txt
   ```

2. Check the error in `backend_logs.txt`

3. Report the specific error message

## Performance Note

Subprocess approach is **slower** than direct generation:
- **Direct (with crashes)**: 0.3-1 second (after first)
- **Subprocess (stable)**: 3-7 seconds (always)

This is expected and acceptable trade-off for stability.

## Next Steps After Success

1. ✅ Generate embeddings for more crops in your session
2. ✅ Try the "Assign to Student" feature
3. ✅ Test clustering functionality
4. ✅ Consider moving to Celery for better performance (future)

---

**Time to test**: 5-10 minutes total  
**Expected outcome**: No more crashes! 🎉
