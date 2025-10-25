# GPU/CUDA Error Fix for Face Embedding Generation

## Problem

When generating face embeddings using DeepFace (which uses TensorFlow), the system was crashing with the following error:

```
CUDA Runtime error: Failed call to cudaGetRuntimeVersion: Error loading CUDA libraries. 
GPU will not be used.
Internal Server Error: /api/attendance/face-crops/253/generate-embedding/
```

## Root Cause

TensorFlow was attempting to use GPU acceleration but:
1. CUDA drivers were not installed on the system
2. The GPU libraries were not available
3. TensorFlow failed to fall back gracefully to CPU mode
4. This caused an Internal Server Error (500) crash

## Solution

### 1. Force CPU-Only Mode

Added environment variables at the beginning of `embedding_service.py` to disable GPU usage:

```python
# Configure TensorFlow to use CPU only (avoid GPU-related errors)
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
```

**Explanation:**
- `CUDA_VISIBLE_DEVICES = '-1'`: Tells TensorFlow no GPU devices are available, forcing CPU usage
- `TF_CPP_MIN_LOG_LEVEL = '2'`: Suppresses informational messages and warnings from TensorFlow

### 2. Improved Error Handling

Enhanced error handling in both `FaceNetModel` and `ArcFaceModel` classes:

```python
except ValueError as e:
    # Re-raise ValueError as is
    raise e
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    raise ValueError(
        f"Failed to generate [Model] embedding: {str(e)}\n"
        f"Make sure the image is a valid face crop. Details: {error_details}"
    ) from e
```

This provides:
- Detailed error messages
- Stack traces for debugging
- Clear indication of what went wrong

### 3. Enhanced Logging

Added comprehensive logging in the view function:

```python
logger.info(f"Generating embedding for crop {crop.id} using {model_name}")
logger.info(f"Processing crop image at: {crop_path}")
logger.info(f"Successfully generated {embedding_obj.dimension}D embedding")
logger.error(f"Failed to generate embedding: {str(e)}", exc_info=True)
```

This helps with:
- Tracking embedding generation progress
- Debugging issues in production
- Monitoring system performance

## Files Modified

1. **`backend/attendance/services/embedding_service.py`**
   - Added CPU-only environment variables
   - Enhanced error handling in `FaceNetModel.generate()`
   - Enhanced error handling in `ArcFaceModel.generate()`

2. **`backend/attendance/views.py`**
   - Added logging to `generate_embedding()` action
   - Improved error messages with more context

## Testing

After applying these changes:

1. **Test Embedding Generation:**
   ```bash
   # Should now work without GPU
   POST /api/attendance/face-crops/{id}/generate-embedding/
   {
     "model_name": "facenet",
     "force_regenerate": false
   }
   ```

2. **Verify CPU Usage:**
   - Check logs for TensorFlow messages
   - Should see: "Could not find cuda drivers... GPU will not be used"
   - But should NOT crash - continues with CPU

3. **Check Performance:**
   - CPU mode is slower than GPU but functional
   - FaceNet: ~1-3 seconds per crop
   - ArcFace: ~2-5 seconds per crop

## Performance Considerations

### CPU vs GPU

**CPU Mode (Current):**
- ✅ Works on any system
- ✅ No special drivers required
- ✅ Reliable and stable
- ⚠️ Slower processing (1-5 seconds per crop)
- ⚠️ May bottleneck with large batches

**GPU Mode (If Available):**
- ✅ Much faster (~0.1-0.5 seconds per crop)
- ✅ Better for large-scale processing
- ❌ Requires CUDA drivers
- ❌ Requires compatible GPU
- ❌ More complex setup

### Recommendations

1. **For Development/Small Classes:**
   - Use CPU mode (current setup)
   - Sufficient for most use cases
   - No additional setup required

2. **For Production/Large Classes:**
   - Consider GPU setup if processing many images
   - Install CUDA drivers and compatible GPU
   - Remove or comment out `CUDA_VISIBLE_DEVICES = '-1'`
   - Significant performance improvement

3. **Alternative Optimization:**
   - Use batch processing endpoints
   - Process crops during off-peak hours
   - Cache embeddings (done automatically)
   - Use FaceNet (128D) instead of ArcFace (512D) for faster processing

## GPU Setup (Optional)

If you want to enable GPU support in the future:

1. **Install CUDA Toolkit:**
   ```bash
   # For Ubuntu/Debian
   wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
   sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
   sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
   sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
   sudo apt-get update
   sudo apt-get -y install cuda
   ```

2. **Install cuDNN:**
   - Download from NVIDIA website
   - Follow installation instructions

3. **Verify Installation:**
   ```bash
   nvidia-smi  # Should show GPU info
   ```

4. **Enable GPU in Code:**
   - Comment out `os.environ['CUDA_VISIBLE_DEVICES'] = '-1'` in `embedding_service.py`
   - Restart Django server
   - Test embedding generation

5. **Install TensorFlow GPU:**
   ```bash
   pip install tensorflow[and-cuda]
   ```

## Troubleshooting

### Still Getting GPU Errors?

1. **Check Environment Variables:**
   ```python
   import os
   print(os.environ.get('CUDA_VISIBLE_DEVICES'))  # Should be '-1'
   ```

2. **Verify TensorFlow Sees No GPU:**
   ```python
   import tensorflow as tf
   print(tf.config.list_physical_devices('GPU'))  # Should be empty
   ```

3. **Test DeepFace Directly:**
   ```python
   from deepface import DeepFace
   result = DeepFace.represent(
       img_path="test_image.jpg",
       model_name="Facenet",
       enforce_detection=False
   )
   ```

### Slow Performance?

1. **Use FaceNet instead of ArcFace:**
   - FaceNet: 128D, faster
   - ArcFace: 512D, slower but more accurate

2. **Process in Batches:**
   - Use batch endpoints for multiple crops
   - Process during off-peak hours

3. **Consider Async Processing:**
   - Use Celery for background tasks
   - Queue embedding generation
   - Process while user does other work

## Monitoring

To monitor embedding generation:

```python
# Check logs
tail -f logs/django.log | grep "embedding"

# Look for:
# "Generating embedding for crop X using facenet"
# "Successfully generated 128D embedding for crop X"
```

## Conclusion

The CPU-only configuration ensures reliable embedding generation on any system without requiring GPU hardware or CUDA drivers. While slower than GPU mode, it's sufficient for most use cases and can be upgraded to GPU when needed for better performance.
