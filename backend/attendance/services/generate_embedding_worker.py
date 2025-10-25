#!/usr/bin/env python
"""
Simplified subprocess worker for generating face embeddings.
This runs in complete isolation from the main Django process.

KEY DESIGN PRINCIPLES:
1. One process per embedding (no caching, no reuse)
2. Minimal environment configuration
3. Explicit cleanup and memory management
4. Clear error reporting with debugging info

Usage:
    python generate_embedding_worker.py <image_path> <model_name> <output_json>
"""

import sys
import os

# CRITICAL: Set environment BEFORE any imports
# Force CPU-only mode (no CUDA)
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Minimal TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Only errors

# Force single-threaded operation to avoid conflicts
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# Disable problematic TensorFlow optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_DISABLE_POOL_ALLOCATOR'] = '1'

# Unbuffered output for immediate logging
os.environ['PYTHONUNBUFFERED'] = '1'

import json
import traceback
import gc


def log_debug(message):
    """Print debug message to stderr"""
    print(f"[WORKER] {message}", file=sys.stderr, flush=True)


def generate_embedding(image_path, model_name, output_file):
    """
    Generate face embedding using DeepFace and save to output file.
    
    Returns:
        0 on success
        1 on error
    """
    deepface_module = None
    
    try:
        log_debug(f"Starting embedding generation")
        log_debug(f"Image: {image_path}")
        log_debug(f"Model: {model_name}")
        log_debug(f"Output: {output_file}")
        
        # Validate inputs
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if model_name not in ['Facenet', 'ArcFace', 'Facenet512']:
            raise ValueError(f"Unsupported model: {model_name}")
        
        # Import DeepFace AFTER environment setup
        log_debug("Importing DeepFace...")
        from deepface import DeepFace
        deepface_module = DeepFace
        
        # Generate embedding
        log_debug("Generating embedding...")
        result = DeepFace.represent(
            img_path=image_path,
            model_name=model_name,
            enforce_detection=False,
            detector_backend='skip',
            align=False  # Skip alignment for pre-cropped faces
        )
        
        log_debug("Extracting embedding vector...")
        
        # Extract embedding vector from result
        embedding = None
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        
        if isinstance(result, dict) and 'embedding' in result:
            embedding = result['embedding']
        else:
            embedding = result
        
        # Convert to list of floats
        if not isinstance(embedding, list):
            embedding = list(embedding)
        
        embedding = [float(x) for x in embedding]
        
        log_debug(f"Embedding generated successfully: {len(embedding)} dimensions")
        
        # Write result to output file
        log_debug("Writing result to file...")
        with open(output_file, 'w') as f:
            json.dump({
                'success': True,
                'embedding': embedding,
                'dimensions': len(embedding),
                'model': model_name
            }, f)
        
        log_debug("Success! Embedding saved.")
        
        # Explicit cleanup
        del embedding
        del result
        del DeepFace
        gc.collect()
        
        return 0
        
    except FileNotFoundError as e:
        error_msg = str(e)
        log_debug(f"File not found error: {error_msg}")
        
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    'success': False,
                    'error': error_msg,
                    'error_type': 'FileNotFoundError',
                    'traceback': traceback.format_exc()
                }, f)
        except Exception as write_error:
            log_debug(f"Failed to write error to file: {write_error}")
            print(f"ERROR: {error_msg}", file=sys.stderr)
        
        return 1
        
    except ValueError as e:
        error_msg = str(e)
        log_debug(f"Value error: {error_msg}")
        
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    'success': False,
                    'error': error_msg,
                    'error_type': 'ValueError',
                    'traceback': traceback.format_exc()
                }, f)
        except Exception as write_error:
            log_debug(f"Failed to write error to file: {write_error}")
            print(f"ERROR: {error_msg}", file=sys.stderr)
        
        return 1
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        log_debug(f"Unexpected error: {error_msg}")
        log_debug(f"Traceback:\n{error_trace}")
        
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    'success': False,
                    'error': error_msg,
                    'error_type': type(e).__name__,
                    'traceback': error_trace
                }, f)
        except Exception as write_error:
            log_debug(f"Failed to write error to file: {write_error}")
            print(f"ERROR: {error_msg}", file=sys.stderr)
        
        return 1
    
    finally:
        # Force cleanup
        if deepface_module:
            del deepface_module
        gc.collect()
        log_debug("Worker cleanup complete")


if __name__ == '__main__':
    # Validate command line arguments
    if len(sys.argv) != 4:
        print("ERROR: Invalid arguments", file=sys.stderr)
        print("Usage: python generate_embedding_worker.py <image_path> <model_name> <output_json>", file=sys.stderr)
        sys.exit(1)
    
    image_path = sys.argv[1]
    model_name = sys.argv[2]
    output_file = sys.argv[3]
    
    # Run embedding generation
    exit_code = generate_embedding(image_path, model_name, output_file)
    
    # Exit with appropriate code
    sys.exit(exit_code)

