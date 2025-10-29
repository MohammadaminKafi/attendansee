import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { CheckCircle, AlertCircle, Sparkles } from 'lucide-react';

export interface EmbeddingGenerationOptions {
  model_name: 'arcface' | 'facenet512';
  process_unprocessed_images: boolean;
  detector_backend: 'opencv' | 'ssd' | 'dlib' | 'mtcnn' | 'retinaface' | 'mediapipe' | 'yolov8' | 'yunet';
  confidence_threshold: number;
  apply_background_effect: boolean;
}

interface EmbeddingGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (options: EmbeddingGenerationOptions) => void;
  isProcessing: boolean;
  unprocessedImagesCount?: number;
  title?: string;
  description?: string;
}

export const EmbeddingGenerationModal: React.FC<EmbeddingGenerationModalProps> = ({
  isOpen,
  onClose,
  onGenerate,
  isProcessing,
  unprocessedImagesCount = 0,
  title = 'Generate Face Embeddings',
  description = 'Generate embeddings for all face crops to enable face recognition and matching.',
}) => {
  const [options, setOptions] = useState<EmbeddingGenerationOptions>({
    model_name: 'arcface',
    process_unprocessed_images: false,
    detector_backend: 'retinaface',
    confidence_threshold: 0.5,
    apply_background_effect: true,
  });

  const handleGenerate = () => {
    onGenerate(options);
  };

  const hasUnprocessedImages = unprocessedImagesCount > 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="space-y-4">
        <p className="text-gray-300">{description}</p>

        {/* Unprocessed Images Warning */}
        {hasUnprocessedImages && (
          <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-warning font-medium mb-2">
                  {unprocessedImagesCount} unprocessed image{unprocessedImagesCount !== 1 ? 's' : ''} found
                </p>
                <p className="text-xs text-warning-light">
                  You can choose to process these images first before generating embeddings,
                  or skip them and only generate embeddings for existing face crops.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Process Unprocessed Images Option */}
        {hasUnprocessedImages && (
          <div className="space-y-3 p-4 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="process-unprocessed"
                checked={options.process_unprocessed_images}
                onChange={(e) =>
                  setOptions({ ...options, process_unprocessed_images: e.target.checked })
                }
                className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
              />
              <label htmlFor="process-unprocessed" className="text-sm text-gray-300 cursor-pointer font-medium">
                Process unprocessed images first
              </label>
            </div>

            {/* Detection Options (shown when processing unprocessed images) */}
            {options.process_unprocessed_images && (
              <div className="ml-6 space-y-3 pt-3 border-t border-dark-border">
                <p className="text-xs text-gray-400 mb-2">Image Processing Options:</p>

                {/* Detector Backend */}
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">
                    Detector Backend
                  </label>
                  <select
                    value={options.detector_backend}
                    onChange={(e) =>
                      setOptions({
                        ...options,
                        detector_backend: e.target.value as EmbeddingGenerationOptions['detector_backend'],
                      })
                    }
                    className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white text-sm focus:outline-none focus:border-primary"
                  >
                    <option value="retinaface">RetinaFace (Recommended)</option>
                    <option value="mtcnn">MTCNN</option>
                    <option value="opencv">OpenCV</option>
                    <option value="ssd">SSD</option>
                    <option value="dlib">Dlib</option>
                    <option value="mediapipe">MediaPipe</option>
                    <option value="yolov8">YOLOv8</option>
                    <option value="yunet">YuNet</option>
                  </select>
                </div>

                {/* Confidence Threshold */}
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">
                    Confidence Threshold: {options.confidence_threshold.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={options.confidence_threshold}
                    onChange={(e) =>
                      setOptions({ ...options, confidence_threshold: parseFloat(e.target.value) })
                    }
                    className="w-full"
                  />
                </div>

                {/* Background Effect */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="background-effect"
                    checked={options.apply_background_effect}
                    onChange={(e) =>
                      setOptions({ ...options, apply_background_effect: e.target.checked })
                    }
                    className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
                  />
                  <label htmlFor="background-effect" className="text-xs text-gray-300 cursor-pointer">
                    Apply background effect
                  </label>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Embedding Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">
            Embedding Model
          </label>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setOptions({ ...options, model_name: 'arcface' })}
              className={`w-full p-4 rounded-lg border transition-colors text-left ${
                options.model_name === 'arcface'
                  ? 'border-primary bg-primary/10'
                  : 'border-dark-border hover:border-gray-600 bg-dark-hover'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <p className="text-white font-medium">ArcFace (512D)</p>
                {options.model_name === 'arcface' && (
                  <CheckCircle className="w-5 h-5 text-primary" />
                )}
              </div>
              <p className="text-xs text-gray-400">
                Higher accuracy, more detailed embeddings. Better for large datasets.
              </p>
            </button>
            <button
              type="button"
              onClick={() => setOptions({ ...options, model_name: 'facenet512' })}
              className={`w-full p-4 rounded-lg border transition-colors text-left ${
                options.model_name === 'facenet512'
                  ? 'border-primary bg-primary/10'
                  : 'border-dark-border hover:border-gray-600 bg-dark-hover'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <p className="text-white font-medium">FaceNet512 (512D)</p>
                {options.model_name === 'facenet512' && (
                  <CheckCircle className="w-5 h-5 text-primary" />
                )}
              </div>
              <p className="text-xs text-gray-400">
                High-dimensional FaceNet variant. Balance between speed and accuracy.
              </p>
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="secondary"
            onClick={onClose}
            className="flex-1"
            disabled={isProcessing}
          >
            Cancel
          </Button>
          <Button
            onClick={handleGenerate}
            disabled={isProcessing}
            className="flex-1"
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Embeddings
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
