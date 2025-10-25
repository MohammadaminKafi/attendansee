# Debugging Subprocess Embedding Issues

## Current Error

```
Subprocess embedding failed: Expecting value: line 1 column 1 (char 0)
```

This means the subprocess is not writing valid JSON to the result file, likely crashing before it can write anything.

## Enhanced Debugging

The updated code now includes:

1. **Better error capture** - Subprocess stderr is logged
2. **File existence checks** - Verifies result file is created and not empty
3. **Detailed logging** - Every step is logged for debugging
4. **Traceback capture** - Subprocess errors include full traceback
5. **Increased timeout** - 120 seconds to allow model downloads
6. **Filtered stderr** - Removes TensorFlow info messages, shows real errors

## Step-by-Step Debugging

### 1. Check Backend Logs

After triggering embedding generation, check logs:

```bash
docker-compose logs backend | tail -100
```

Look for:
- `Running embedding generation in subprocess`
- `Subprocess stderr` (will show actual error)
- `Subprocess traceback` (will show where it failed)

### 2. Test Manually

Run the test script:

```bash
# Find a face crop file
docker-compose exec backend ls -la /app/media/face_crops/

# Test with specific crop
docker-compose exec backend python test_subprocess_embedding.py /app/media/face_crops/crop_xxx.jpg
```

This will show exactly what's happening.

### 3. Test DeepFace Directly

Test if DeepFace works at all in the container:

```bash
docker-compose exec backend python -c "
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print('Importing DeepFace...')
from deepface import DeepFace
print('✓ DeepFace imported successfully')

# Try to build model
print('Building Facenet model...')
model = DeepFace.build_model('Facenet')
print('✓ Model built successfully')
print(f'Model type: {type(model)}')
"
```

**Expected output:**
```
Importing DeepFace...
✓ DeepFace imported successfully
Building Facenet model...
✓ Model built successfully
Model type: <class 'keras.src.engine.functional.Functional'>
```

**If this fails**, DeepFace is not properly installed.

### 4. Test DeepFace.represent

Test the actual function we're calling:

```bash
docker-compose exec backend python -c "
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from deepface import DeepFace

# Use any existing image file
image_path = '/app/media/face_crops/crop_xxx.jpg'  # Replace with real file

print(f'Testing DeepFace.represent with: {image_path}')

result = DeepFace.represent(
    img_path=image_path,
    model_name='Facenet',
    enforce_detection=False,
    detector_backend='skip'
)

print(f'✓ Result type: {type(result)}')
print(f'✓ Result structure: {type(result[0]) if isinstance(result, list) else type(result)}')

if isinstance(result, list) and len(result) > 0:
    result = result[0]

if isinstance(result, dict) and 'embedding' in result:
    embedding = result['embedding']
    print(f'✓ Embedding dimension: {len(embedding)}')
    print(f'✓ First 5 values: {embedding[:5]}')
else:
    print(f'✗ Unexpected result structure: {result}')
"
```

### 5. Check Python Executable

Verify subprocess can find Python:

```bash
docker-compose exec backend python -c "
import sys
print(f'Python executable: {sys.executable}')
print(f'Python version: {sys.version}')

# Test subprocess
import subprocess
result = subprocess.run([sys.executable, '-c', 'print(\"test\")'], capture_output=True)
print(f'Subprocess test: {result.stdout.decode()}')
"
```

### 6. Check File Permissions

```bash
docker-compose exec backend python -c "
import tempfile
import os

# Test temp file creation
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    temp_file = f.name
    f.write('{\"test\": true}')

print(f'Created temp file: {temp_file}')
print(f'File exists: {os.path.exists(temp_file)}')
print(f'File size: {os.path.getsize(temp_file)}')

# Read it back
with open(temp_file, 'r') as f:
    content = f.read()
    print(f'File content: {content}')

# Clean up
os.unlink(temp_file)
print('✓ Temp file operations work')
"
```

## Common Issues and Solutions

### Issue 1: DeepFace Not Found

**Error:** `ModuleNotFoundError: No module named 'deepface'`

**Solution:**
```bash
# Reinstall deepface
docker-compose exec backend pip install deepface --upgrade
docker-compose restart backend
```

### Issue 2: TensorFlow Issues

**Error:** Various TensorFlow errors

**Solution:**
```bash
# Check TensorFlow version
docker-compose exec backend python -c "import tensorflow as tf; print(tf.__version__)"

# If missing or wrong version
docker-compose exec backend pip install tensorflow==2.15.0
docker-compose restart backend
```

### Issue 3: Model Download Fails

**Error:** Network or download errors

**Solution:**
```bash
# Pre-download models
docker-compose exec backend python -c "
from deepface import DeepFace
print('Downloading Facenet...')
DeepFace.build_model('Facenet')
print('Downloading ArcFace...')
DeepFace.build_model('ArcFace')
print('✓ Models downloaded')
"
```

### Issue 4: Path Issues

**Error:** File not found errors

**Solution:**
```bash
# Check if file exists
docker-compose exec backend ls -la /app/media/face_crops/

# Check Django media root
docker-compose exec backend python manage.py shell -c "
from django.conf import settings
print(f'MEDIA_ROOT: {settings.MEDIA_ROOT}')
import os
print(f'Exists: {os.path.exists(settings.MEDIA_ROOT)}')
print(f'Contents: {os.listdir(settings.MEDIA_ROOT)}')
"
```

### Issue 5: Subprocess Crashes Silently

**Error:** Empty JSON file

**Check:** Look for stderr file next to result file:

```bash
# The code now saves stderr to {result_file}.stderr
# Check backend logs for the path
docker-compose logs backend | grep "stderr saved"

# Read the stderr file
docker-compose exec backend cat /tmp/tmpXXXXXX.json.stderr
```

## Manual Subprocess Test

Create a test file to replicate the subprocess exactly:

```python
# save as test_manual_subprocess.py
import subprocess
import sys
import json
import tempfile
import os

image_path = '/app/media/face_crops/crop_123.jpg'  # Replace with real file
model_name = 'Facenet'

with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    temp_result_file = f.name

script = f"""
import os
import sys
import json
import traceback

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

result_file = {repr(temp_result_file)}
image_path = {repr(image_path)}
model_name = {repr(model_name)}

try:
    from deepface import DeepFace
    
    result = DeepFace.represent(
        img_path=image_path,
        model_name=model_name,
        enforce_detection=False,
        detector_backend='skip'
    )
    
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
    
    if isinstance(result, dict) and 'embedding' in result:
        embedding = result['embedding']
    else:
        embedding = list(result)
    
    embedding = [float(x) for x in embedding]
    
    with open(result_file, 'w') as f:
        json.dump({{'embedding': embedding, 'success': True}}, f)
    
    sys.exit(0)
    
except Exception as e:
    error_msg = str(e)
    error_trace = traceback.format_exc()
    
    try:
        with open(result_file, 'w') as f:
            json.dump({{'error': error_msg, 'traceback': error_trace, 'success': False}}, f)
    except:
        pass
    
    sys.exit(1)
"""

print("Running subprocess...")
process = subprocess.Popen(
    [sys.executable, '-c', script],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

stdout, stderr = process.communicate(timeout=120)
print(f"Return code: {process.returncode}")
print(f"Stdout: {stdout.decode()}")
print(f"Stderr: {stderr.decode()}")

if os.path.exists(temp_result_file):
    with open(temp_result_file, 'r') as f:
        result = json.load(f)
    print(f"Result: {result}")
else:
    print("ERROR: Result file not created")

# Clean up
try:
    os.unlink(temp_result_file)
except:
    pass
```

Run it:
```bash
docker-compose exec backend python test_manual_subprocess.py
```

## What to Report

If still not working, collect:

1. **Full backend logs:**
   ```bash
   docker-compose logs backend > backend_full.log
   ```

2. **DeepFace test result:**
   ```bash
   docker-compose exec backend python -c "from deepface import DeepFace; print(DeepFace.__version__)" 2>&1 > deepface_test.log
   ```

3. **Manual subprocess test result:**
   ```bash
   docker-compose exec backend python test_manual_subprocess.py > subprocess_test.log 2>&1
   ```

4. **Environment info:**
   ```bash
   docker-compose exec backend python -c "
   import sys
   import tensorflow as tf
   import deepface
   print(f'Python: {sys.version}')
   print(f'TensorFlow: {tf.__version__}')
   print(f'DeepFace: {deepface.__version__}')
   " > env_info.log 2>&1
   ```

Send all 4 files for analysis.

---

**Next Steps:**

1. Try the debugging steps above
2. Look at backend logs for the actual error
3. Test DeepFace directly in the container
4. Report specific error messages found
