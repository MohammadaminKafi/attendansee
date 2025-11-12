import React, { useState, useEffect } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { ChevronLeft, ChevronRight, UserCheck, X as XIcon, AlertCircle, CheckCircle } from 'lucide-react';
import { faceCropsAPI } from '@/services/api';

interface SimilarFace {
  crop_id: number;
  student_id: number | null;
  student_name: string | null;
  similarity: number;
  distance: number | null;
  crop_image_path: string;
  is_identified: boolean;
}

interface CropSuggestion {
  crop_id: number;
  crop_image_path: string | null;
  image_id: number;
  similar_faces: SimilarFace[];
}

interface ManualAssignModalProps {
  isOpen: boolean;
  onClose: () => void;
  suggestions: CropSuggestion[];
  onUpdate: () => void;
}

export const ManualAssignModal: React.FC<ManualAssignModalProps> = ({
  isOpen,
  onClose,
  suggestions,
  onUpdate,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [assignedCrops, setAssignedCrops] = useState<Set<number>>(new Set());

  // Reset to first unassigned crop when modal opens
  useEffect(() => {
    if (isOpen && suggestions.length > 0) {
      const firstUnassigned = suggestions.findIndex(s => !assignedCrops.has(s.crop_id));
      if (firstUnassigned !== -1) {
        setCurrentIndex(firstUnassigned);
      }
    }
  }, [isOpen]);

  const currentCrop = suggestions[currentIndex];
  const totalCrops = suggestions.length;
  const remainingCrops = totalCrops - assignedCrops.size;
  const progressPercent = totalCrops > 0 ? (assignedCrops.size / totalCrops) * 100 : 0;

  const handleNext = () => {
    if (currentIndex < suggestions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handleSkip = () => {
    if (currentIndex < suggestions.length - 1) {
      handleNext();
    } else {
      // At the last crop, go to first unassigned or close
      const firstUnassigned = suggestions.findIndex(s => !assignedCrops.has(s.crop_id));
      if (firstUnassigned !== -1 && firstUnassigned !== currentIndex) {
        setCurrentIndex(firstUnassigned);
      } else {
        // All done
        onUpdate();
        onClose();
      }
    }
  };

  const handleAssignFromSuggestion = async (candidateCropId: number, similarity: number) => {
    if (!currentCrop) return;

    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);

      const result = await faceCropsAPI.assignFromCandidate(
        currentCrop.crop_id,
        candidateCropId,
        similarity
      );

      if (result.assigned && result.student_name) {
        setSuccessMessage(`Assigned to ${result.student_name}`);
        setAssignedCrops(prev => new Set(prev).add(currentCrop.crop_id));
        
        // Move to next unassigned crop after a short delay
        setTimeout(() => {
          const nextUnassigned = suggestions.findIndex(
            (s, idx) => idx > currentIndex && !assignedCrops.has(s.crop_id)
          );
          if (nextUnassigned !== -1) {
            setCurrentIndex(nextUnassigned);
          } else {
            // Check if there are any unassigned crops before current
            const prevUnassigned = suggestions.findIndex(s => !assignedCrops.has(s.crop_id));
            if (prevUnassigned !== -1) {
              setCurrentIndex(prevUnassigned);
            } else {
              // All crops assigned, close modal
              onUpdate();
              onClose();
            }
          }
          setSuccessMessage(null);
        }, 800);
      } else {
        setError(result.message || 'Failed to assign crop');
      }
    } catch (err: any) {
      console.error('Error assigning from candidate:', err);
      setError(err.response?.data?.error || 'Failed to assign crop');
    } finally {
      setProcessing(false);
    }
  };

  const getImageUrl = (path: string | null) => {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  };

  if (!currentCrop) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="Manual Assignment" className="max-w-md">
        <div className="text-center py-6">
          <p className="text-gray-400 text-sm">No unidentified crops found to assign.</p>
          <Button onClick={onClose} className="mt-3">Close</Button>
        </div>
      </Modal>
    );
  }

  const isCurrentCropAssigned = assignedCrops.has(currentCrop.crop_id);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Manual Face Assignment" className="max-w-4xl">
      <div className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">
              Assignment Progress: {assignedCrops.size} / {totalCrops} completed
            </span>
            <span className="text-primary font-medium">{progressPercent.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-dark-border rounded-full h-2 overflow-hidden">
            <div
              className="bg-primary h-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 text-center">
            {remainingCrops} crop{remainingCrops !== 1 ? 's' : ''} remaining
          </p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="p-2.5 bg-success/10 border border-success/20 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />
            <p className="text-xs text-success-light">{successMessage}</p>
            <button onClick={() => setSuccessMessage(null)} className="ml-auto text-success-light hover:text-success">
              <XIcon className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-2.5 bg-danger/10 border border-danger/20 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" />
            <p className="text-xs text-danger-light">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-danger-light hover:text-danger">
              <XIcon className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Current Crop Display */}
        <div className="border border-dark-border rounded-lg overflow-hidden">
          <div className="bg-dark-hover p-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white">
                Unidentified Face #{currentIndex + 1}
                {isCurrentCropAssigned && (
                  <span className="ml-2 text-xs font-normal text-success">(Assigned)</span>
                )}
              </h3>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handlePrevious}
                  disabled={currentIndex === 0}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-xs text-gray-400 min-w-[70px] text-center">
                  {currentIndex + 1} / {totalCrops}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleNext}
                  disabled={currentIndex === totalCrops - 1}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
          <div className="p-4 bg-dark-bg">
            <div className="w-48 h-48 mx-auto bg-dark-hover rounded-lg overflow-hidden border-2 border-primary/30">
              <img
                src={getImageUrl(currentCrop.crop_image_path)}
                alt={`Crop ${currentCrop.crop_id}`}
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        </div>

        {/* Similar Faces Grid */}
        <div className="border border-dark-border rounded-lg overflow-hidden">
          <div className="bg-dark-hover p-3">
            <h3 className="text-base font-semibold text-white">
              Top-5 Similar Faces - Choose One to Assign
            </h3>
            <p className="text-xs text-gray-400 mt-1">
              Select a face to assign the same student to the current crop
            </p>
          </div>
          <div className="p-4 bg-dark-bg">
            {currentCrop.similar_faces.length === 0 ? (
              <div className="text-center py-6">
                <AlertCircle className="w-10 h-10 text-gray-500 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">No similar faces found</p>
                <p className="text-xs text-gray-500 mt-1">
                  This crop may need more labeled data in the class
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {currentCrop.similar_faces.map((face) => (
                  <div
                    key={face.crop_id}
                    className={`rounded-lg border overflow-hidden transition-all ${
                      face.student_id
                        ? 'border-primary/30 hover:border-primary bg-dark-hover'
                        : 'border-dark-border bg-dark-card opacity-60'
                    }`}
                  >
                    <div className="aspect-square bg-dark-bg">
                      <img
                        src={getImageUrl(face.crop_image_path)}
                        alt={`Similar face ${face.crop_id}`}
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <div className="p-2 space-y-1.5">
                      <div className="min-h-[36px]">
                        {face.student_name ? (
                          <p className="text-xs font-medium text-white line-clamp-2">
                            {face.student_name}
                          </p>
                        ) : (
                          <p className="text-xs text-gray-500 italic">Unassigned</p>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400">Similarity:</span>
                        <span className="text-primary font-medium">
                          {(face.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      {face.student_id ? (
                        <Button
                          size="sm"
                          onClick={() => handleAssignFromSuggestion(face.crop_id, face.similarity)}
                          disabled={processing || isCurrentCropAssigned}
                          className="w-full"
                        >
                          <UserCheck className="w-3 h-3 mr-1" />
                          Assign
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled
                          className="w-full"
                        >
                          No Student
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-3 border-t border-dark-border">
          <Button variant="secondary" onClick={onClose} className="flex-1" disabled={processing}>
            Close & Save Progress
          </Button>
          <Button
            variant="secondary"
            onClick={handleSkip}
            className="flex-1"
            disabled={processing}
          >
            Skip This Crop
          </Button>
        </div>
      </div>
    </Modal>
  );
};
