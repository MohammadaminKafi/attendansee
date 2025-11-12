import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { CheckCircle, AlertCircle, UserCheck, XCircle } from 'lucide-react';
import { AutoAssignAllCropsResponse } from '@/types';

export interface AutoAssignOptions {
  k: number;
  similarity_threshold: number;
  embedding_model: 'arcface' | 'facenet512';
  use_voting: boolean;
}

interface AutoAssignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAutoAssign: (options: AutoAssignOptions) => void;
  isProcessing: boolean;
  cropsWithoutEmbeddings?: number;
  unidentifiedCropsCount?: number;
  title?: string;
  description?: string;
}

interface AutoAssignResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: AutoAssignAllCropsResponse;
}

export const AutoAssignModal: React.FC<AutoAssignModalProps> = ({
  isOpen,
  onClose,
  onAutoAssign,
  isProcessing,
  cropsWithoutEmbeddings = 0,
  unidentifiedCropsCount = 0,
  title = 'Auto-Assign All Face Crops',
  description = 'Automatically assign all unidentified face crops to students based on similarity matching.',
}) => {
  const [options, setOptions] = useState<AutoAssignOptions>({
    k: 5,
    similarity_threshold: 0.6,
    embedding_model: 'arcface',
    use_voting: false,
  });

  const handleAutoAssign = () => {
    onAutoAssign(options);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} className="max-w-xl">
      <div className="space-y-4">
        {/* Description */}
        <p className="text-gray-300 text-sm">{description}</p>

        {/* Status Information */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-dark-hover rounded-lg border border-dark-border">
            <p className="text-xs text-gray-400 mb-1">Unidentified Crops</p>
            <p className="text-xl font-bold text-white">{unidentifiedCropsCount}</p>
          </div>
          <div className="p-3 bg-dark-hover rounded-lg border border-dark-border">
            <p className="text-xs text-gray-400 mb-1">Need Embeddings</p>
            <p className="text-xl font-bold text-warning">{cropsWithoutEmbeddings}</p>
          </div>
        </div>

        {/* Warning if crops need embeddings */}
        {cropsWithoutEmbeddings > 0 && (
          <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-warning-light">
                {cropsWithoutEmbeddings} face crop{cropsWithoutEmbeddings !== 1 ? 's' : ''} don't have embeddings yet. 
                Generate embeddings first for better results.
              </p>
            </div>
          </div>
        )}

        {/* Configuration Options */}
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-white">Assignment Parameters</h3>

          {/* K Value */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5">
              Number of Neighbors (K)
            </label>
            <input
              type="number"
              value={options.k}
              onChange={(e) => setOptions({ ...options, k: parseInt(e.target.value) || 5 })}
              min={1}
              max={20}
              className="w-full px-3 py-1.5 bg-dark-bg border border-dark-border rounded-lg text-white text-sm focus:outline-none focus:border-primary"
            />
            <p className="text-xs text-gray-500 mt-1">
              Number of similar faces to consider (1-20).
            </p>
          </div>

          {/* Similarity Threshold */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5">
              Similarity Threshold ({(options.similarity_threshold * 100).toFixed(0)}%)
            </label>
            <input
              type="range"
              value={options.similarity_threshold}
              onChange={(e) =>
                setOptions({ ...options, similarity_threshold: parseFloat(e.target.value) })
              }
              min={0.3}
              max={0.95}
              step={0.05}
              className="w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer"
              style={{
                accentColor: 'var(--color-primary)',
              }}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>30% (Loose)</span>
              <span>60% (Balanced)</span>
              <span>95% (Strict)</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Minimum similarity score required for assignment. Lower values assign more crops but may have errors.
            </p>
          </div>

          {/* Embedding Model */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5">
              Embedding Model
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setOptions({ ...options, embedding_model: 'arcface' })}
                className={`p-2 rounded-lg border transition-colors text-left ${
                  options.embedding_model === 'arcface'
                    ? 'border-primary bg-primary/10'
                    : 'border-dark-border hover:border-gray-600 bg-dark-hover'
                }`}
              >
                <div className="flex items-center justify-between mb-0.5">
                  <p className="text-white font-medium text-xs">ArcFace</p>
                  {options.embedding_model === 'arcface' && (
                    <CheckCircle className="w-3 h-3 text-primary" />
                  )}
                </div>
                <p className="text-xs text-gray-400">Higher accuracy</p>
              </button>
              <button
                onClick={() => setOptions({ ...options, embedding_model: 'facenet512' })}
                className={`p-2 rounded-lg border transition-colors text-left ${
                  options.embedding_model === 'facenet512'
                    ? 'border-primary bg-primary/10'
                    : 'border-dark-border hover:border-gray-600 bg-dark-hover'
                }`}
              >
                <div className="flex items-center justify-between mb-0.5">
                  <p className="text-white font-medium text-xs">FaceNet512</p>
                  {options.embedding_model === 'facenet512' && (
                    <CheckCircle className="w-3 h-3 text-primary" />
                  )}
                </div>
                <p className="text-xs text-gray-400">Balanced</p>
              </button>
            </div>
          </div>

          {/* Use Voting */}
          <div className="flex items-center gap-2 p-2 bg-dark-hover rounded-lg border border-dark-border">
            <input
              type="checkbox"
              id="use-voting"
              checked={options.use_voting}
              onChange={(e) => setOptions({ ...options, use_voting: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
            />
            <label htmlFor="use-voting" className="text-xs text-gray-300 cursor-pointer flex-1">
              <span className="font-medium text-white">Use Majority Voting</span>
              <p className="text-xs text-gray-500 mt-0.5">
                Consider the most common student among K neighbors.
              </p>
            </label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4 border-t border-dark-border">
          <Button
            variant="secondary"
            onClick={onClose}
            className="flex-1"
            disabled={isProcessing}
          >
            Cancel
          </Button>
          <Button
            onClick={handleAutoAssign}
            disabled={isProcessing || unidentifiedCropsCount === 0}
            className="flex-1"
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Processing...
              </>
            ) : (
              <>
                <UserCheck className="w-4 h-4 mr-2" />
                Auto-Assign All
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export const AutoAssignResultModal: React.FC<AutoAssignResultModalProps> = ({
  isOpen,
  onClose,
  result,
}) => {
  const [showAssignedDetails, setShowAssignedDetails] = useState(false);
  const [showUnassignedDetails, setShowUnassignedDetails] = useState(false);

  const getImageUrl = (path: string | null) => {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  };

  const assignmentRate = result.crops_to_process > 0 
    ? (result.crops_assigned / result.crops_to_process) * 100 
    : 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Auto-Assignment Complete" className="max-w-3xl">
      <div className="space-y-4">
        {/* Success Banner */}
        <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-6 h-6 text-success flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-success font-medium mb-1">
                Auto-assignment completed successfully!
              </p>
              <p className="text-sm text-success-light">
                {result.crops_assigned} out of {result.crops_to_process} face crops were assigned to students
                ({assignmentRate.toFixed(1)}% success rate)
              </p>
            </div>
          </div>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 bg-dark-hover rounded-lg border border-dark-border">
            <p className="text-xs text-gray-400 mb-1">Processed</p>
            <p className="text-xl font-bold text-white">{result.crops_to_process}</p>
          </div>
          <div className="p-3 bg-success/10 rounded-lg border border-success/20">
            <p className="text-xs text-gray-400 mb-1">Assigned</p>
            <p className="text-xl font-bold text-success">{result.crops_assigned}</p>
          </div>
          <div className="p-3 bg-warning/10 rounded-lg border border-warning/20">
            <p className="text-xs text-gray-400 mb-1">Unassigned</p>
            <p className="text-xl font-bold text-warning">{result.crops_unassigned}</p>
          </div>
          <div className="p-3 bg-dark-hover rounded-lg border border-dark-border">
            <p className="text-xs text-gray-400 mb-1">Success Rate</p>
            <p className="text-xl font-bold text-primary">{assignmentRate.toFixed(0)}%</p>
          </div>
        </div>

        {/* Parameters Used */}
        <div className="p-3 bg-dark-hover rounded-lg border border-dark-border">
          <h3 className="text-xs font-semibold text-white mb-2">Parameters Used</h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-gray-400">K Neighbors:</span>
              <span className="text-white ml-2 font-medium">{result.parameters.k}</span>
            </div>
            <div>
              <span className="text-gray-400">Threshold:</span>
              <span className="text-white ml-2 font-medium">
                {(result.parameters.similarity_threshold * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="text-gray-400">Model:</span>
              <span className="text-white ml-2 font-medium">
                {result.parameters.embedding_model || 'arcface'}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Voting:</span>
              <span className="text-white ml-2 font-medium">
                {result.parameters.use_voting ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>

        {/* Assigned Crops Details */}
        {result.assigned_crops.length > 0 && (
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <button
              onClick={() => setShowAssignedDetails(!showAssignedDetails)}
              className="w-full p-4 bg-dark-hover hover:bg-dark-card transition-colors flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-success" />
                <span className="font-medium text-white">
                  Assigned Crops ({result.assigned_crops.length})
                </span>
              </div>
              <span className="text-gray-400">
                {showAssignedDetails ? '▼' : '▶'}
              </span>
            </button>
            {showAssignedDetails && (
              <div className="p-4 bg-dark-bg max-h-96 overflow-y-auto">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {result.assigned_crops.map((crop) => (
                    <div key={crop.crop_id} className="bg-dark-hover rounded-lg overflow-hidden border border-dark-border">
                      <div className="aspect-square bg-dark-bg">
                        <img
                          src={getImageUrl(crop.crop_image_path)}
                          alt={`Crop ${crop.crop_id}`}
                          className="w-full h-full object-contain"
                        />
                      </div>
                      <div className="p-2">
                        <p className="text-xs text-white font-medium truncate">
                          {crop.student_name}
                        </p>
                        {crop.confidence && (
                          <p className="text-xs text-gray-400">
                            {(crop.confidence * 100).toFixed(0)}% confidence
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Unassigned Crops Details */}
        {result.unassigned_crops.length > 0 && (
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <button
              onClick={() => setShowUnassignedDetails(!showUnassignedDetails)}
              className="w-full p-4 bg-dark-hover hover:bg-dark-card transition-colors flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-warning" />
                <span className="font-medium text-white">
                  Unassigned Crops ({result.unassigned_crops.length})
                </span>
              </div>
              <span className="text-gray-400">
                {showUnassignedDetails ? '▼' : '▶'}
              </span>
            </button>
            {showUnassignedDetails && (
              <div className="p-4 bg-dark-bg max-h-96 overflow-y-auto">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {result.unassigned_crops.map((crop) => (
                    <div key={crop.crop_id} className="bg-dark-hover rounded-lg overflow-hidden border border-warning/30">
                      <div className="aspect-square bg-dark-bg">
                        <img
                          src={getImageUrl(crop.crop_image_path)}
                          alt={`Crop ${crop.crop_id}`}
                          className="w-full h-full object-contain"
                        />
                      </div>
                      <div className="p-2">
                        <p className="text-xs text-gray-400 line-clamp-2">
                          {crop.reason}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4 border-t border-dark-border">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};
