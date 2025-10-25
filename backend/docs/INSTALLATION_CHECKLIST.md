# Installation Checklist - Embedding Service Rewrite

## ⚠️ IMPORTANT: Follow These Steps

### □ Step 1: Read the Documentation (5 minutes)

Before installing, quickly read:
- [ ] `EMBEDDING_SERVICE_SUMMARY.md` - Overview of what changed
- [ ] `EMBEDDING_SERVICE_QUICK_START.md` - Installation steps

### □ Step 2: Backup Current Files (1 minute)

```bash
cd backend/attendance/services

# On Linux/WSL:
cp embedding_service.py embedding_service_old.py.backup

# On Windows:
# Just make a copy of embedding_service.py with a different name
```

### □ Step 3: Replace the Embedding Service File (1 minute)

**On Linux/WSL:**
```bash
cd backend/attendance/services
mv embedding_service.py embedding_service_old.py
mv embedding_service_new.py embedding_service.py
```

**On Windows PowerShell:**
```powershell
cd F:\Programming\Projects\AttendanSee\backend\attendance\services
Move-Item "embedding_service.py" "embedding_service_old.py" -Force
Move-Item "embedding_service_new.py" "embedding_service.py" -Force
```

**Or manually in File Explorer:**
1. Rename `embedding_service.py` to `embedding_service_old.py`
2. Rename `embedding_service_new.py` to `embedding_service.py`

### □ Step 4: Verify Files Are in Place (1 minute)

Check that these files exist:
- [ ] `backend/attendance/services/embedding_service.py` (new version)
- [ ] `backend/attendance/services/generate_embedding_worker.py` (updated)
- [ ] `backend/attendance/services/embedding_service_old.py` (backup)

### □ Step 5: Restart Django Server (1 minute)

```bash
# Stop current server (Ctrl+C)
# Then restart:
python manage.py runserver
```

- [ ] Django starts without errors
- [ ] No import errors
- [ ] Server is running

### □ Step 6: Test Single Embedding (2 minutes)

From your frontend or using curl:

```bash
curl -X POST http://localhost:8000/api/attendance/face-crops/253/generate-embedding/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"model_name": "facenet", "force_regenerate": true}'
```

Expected response:
```json
{
  "status": "success",
  "crop_id": 253,
  "embedding_model": "facenet",
  "embedding_dimension": 128,
  "message": "Embedding generated successfully"
}
```

### □ Step 7: Check Django Console Output (1 minute)

Look for these messages in your Django console:

- [ ] `[WORKER] Starting embedding generation`
- [ ] `[WORKER] Generating embedding...`
- [ ] `[WORKER] Embedding generated successfully: 128 dimensions`
- [ ] `[WORKER] Success! Embedding saved.`
- [ ] `Subprocess completed in X.XXs with code 0`
- [ ] NO "double free" errors
- [ ] NO "Subprocess exited with code: -6"

### □ Step 8: Test Batch Processing (3 minutes)

Try generating embeddings for multiple crops:

```bash
curl -X POST http://localhost:8000/api/attendance/face-crops/generate-embeddings-batch/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "face_crop_ids": [253, 254, 255],
    "model_name": "facenet",
    "force_regenerate": true
  }'
```

- [ ] All embeddings generate successfully
- [ ] No errors in console
- [ ] Response shows success count

### □ Step 9: Monitor Memory Usage (5 minutes)

While generating embeddings, watch your system's memory usage:

**On Linux:**
```bash
watch -n 1 "ps aux | grep 'manage.py runserver'"
```

**On Windows:**
- Open Task Manager
- Find Python process
- Watch memory usage

- [ ] Memory usage is stable
- [ ] No continuous growth
- [ ] Memory returns to baseline after embeddings complete

### □ Step 10: Test Error Handling (2 minutes)

Try to generate an embedding for a non-existent crop:

```bash
curl -X POST http://localhost:8000/api/attendance/face-crops/99999/generate-embedding/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"model_name": "facenet"}'
```

- [ ] Gets clear error message (not generic "Bad Request")
- [ ] Error type is specified
- [ ] Logs show detailed error information

### □ Step 11: Test Frontend Integration (3 minutes)

From your frontend:
1. Go to a session with face crops
2. Select an unidentified face crop
3. Click "Generate Embedding" (or equivalent action)

- [ ] Embedding generates successfully
- [ ] UI updates correctly
- [ ] No errors in browser console
- [ ] No errors in Django console

### □ Step 12: Full Session Test (5 minutes)

Process a complete session:
1. Upload images to a session
2. Process images (face detection)
3. Generate embeddings for all crops
4. Run clustering or assignment

- [ ] All steps complete successfully
- [ ] No crashes or hangs
- [ ] Memory stable throughout process
- [ ] Clear progress in logs

## ✅ Success Criteria

You're good to go if:

- [x] No more "double free" errors
- [x] Embeddings generate successfully
- [x] Clear error messages in logs
- [x] Memory usage is stable
- [x] Django doesn't crash
- [x] Frontend integration works
- [x] Batch processing works
- [x] Process can run continuously without issues

## ❌ If Something Goes Wrong

### Option 1: Check the Documentation

- Read `EMBEDDING_SERVICE_REWRITE.md` for troubleshooting
- Look at `EMBEDDING_SERVICE_COMPARISON.md` to understand changes

### Option 2: Debug

1. Check Django console for errors
2. Look for `[WORKER]` messages
3. Check if both files are in place
4. Verify Python can import the module

### Option 3: Test Worker Directly

```bash
python backend/attendance/services/generate_embedding_worker.py \
  /path/to/actual/face/crop.jpg \
  Facenet \
  /tmp/test_result.json

cat /tmp/test_result.json
```

If this works, the problem is in Django integration.

### Option 4: Rollback

```bash
cd backend/attendance/services
mv embedding_service.py embedding_service_broken.py
mv embedding_service_old.py embedding_service.py
# Restart Django
```

Then report the issue with:
- Django console output
- Worker output
- Any error messages

## 📊 Performance Benchmarks

After installation, you should see:

| Metric | Expected Value |
|--------|----------------|
| Single embedding time | 2-4 seconds |
| Memory per embedding | ~500MB (subprocess) |
| Django memory growth | None (stable) |
| Error rate | 0% for valid images |
| Crash rate | 0% |
| Double free errors | 0 |

## 🎉 Completion

Once all checkboxes are marked:

- [ ] **Installation complete!**
- [ ] **Service is working correctly!**
- [ ] **No more double free errors!**
- [ ] **Code is simpler and cleaner!**
- [ ] **Debugging is easier!**

**Congratulations! Your embedding service is now:**
- ✅ Stable
- ✅ Reliable  
- ✅ Simple
- ✅ Well-documented
- ✅ Easy to debug

## 📚 Reference Documents

For future reference:

1. **EMBEDDING_SERVICE_SUMMARY.md** - Quick overview
2. **EMBEDDING_SERVICE_QUICK_START.md** - Installation guide
3. **EMBEDDING_SERVICE_REWRITE.md** - Complete documentation
4. **EMBEDDING_SERVICE_COMPARISON.md** - Detailed before/after

## Support

If you need help:
1. Check the documentation in `backend/docs/`
2. Look for `[WORKER]` messages in logs
3. Test the worker script directly
4. Review the comparison document to understand changes

---

**Time to complete:** ~30 minutes
**Difficulty:** Easy
**Risk:** Low (can rollback)
**Benefit:** No more crashes, simpler code, better debugging

**Now go install it and enjoy stable embeddings!** 🚀
