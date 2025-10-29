import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { faceCropsAPI } from '@/services/api';
import { FaceCropDetail } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import {
  ArrowLeft,
  Sparkles,
  UserCheck,
  CheckCircle,
  AlertCircle,
  Image as ImageIcon,
  Calendar,
  User,
  Hash,
  XCircle,
  X as XIcon,
} from 'lucide-react';

const FaceCropDetailPage: React.FC = () => {
  const { classId, sessionId, imageId, cropId } = useParams<{
    classId: string;
    sessionId: string;
    imageId: string;
    cropId: string;
  }>();
  const navigate = useNavigate();

  // Data states
  const [crop, setCrop] = useState<FaceCropDetail | null>(null);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showFullEmbedding, setShowFullEmbedding] = useState(false);

  // Modal states
  const [showEmbeddingModal, setShowEmbeddingModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState<'arcface' | 'facenet512'>('arcface');

  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignOptions, setAssignOptions] = useState({
    k: 5,
    similarity_threshold: 0.6,
    embedding_model: 'arcface' as 'arcface' | 'facenet512',
    use_voting: true,
  });

  // Suggestions modal
  const [showSuggestModal, setShowSuggestModal] = useState(false);
  const [suggestions, setSuggestions] = useState<Array<{
    crop_id: number;
    student_id: number | null;
    student_name: string | null;
    similarity: number;
    distance: number | null;
    crop_image_path: string;
    is_identified: boolean;
  }>>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    loadData();
  }, [cropId]);

  const loadData = async () => {
    if (!cropId || !classId) return;

    try {
      setLoading(true);
      setError(null);

      const cropData = await faceCropsAPI.getFaceCrop(parseInt(cropId));

      setCrop(cropData);
    } catch (err: any) {
      console.error('Error loading crop data:', err);
      setError(err.response?.data?.detail || 'Failed to load crop data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateEmbedding = async () => {
    if (!cropId) return;

    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);

      const result = await faceCropsAPI.generateEmbedding(
        parseInt(cropId),
        selectedModel
      );

      setSuccessMessage(
        `Successfully generated ${result.embedding_dimension}D embedding using ${result.model_name} model`
      );

      // Reload crop data to get updated embedding_model field
      await loadData();
      setShowEmbeddingModal(false);
    } catch (err: any) {
      console.error('Error generating embedding:', err);
      setError(err.response?.data?.error || 'Failed to generate embedding');
    } finally {
      setProcessing(false);
    }
  };

  const handleAssignCrop = async () => {
    if (!cropId) return;

    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);

      const result = await faceCropsAPI.assignCrop(parseInt(cropId), {
        ...assignOptions,
        auto_commit: true,
      });

      if (result.assigned && result.student_name) {
        setSuccessMessage(
          `Successfully assigned crop to ${result.student_name} (confidence: ${(result.confidence! * 100).toFixed(1)}%)`
        );
      } else {
        setError(result.message || 'Could not find a suitable match for this crop');
      }

      // Reload crop data to get updated student assignment
      await loadData();
      setShowAssignModal(false);
    } catch (err: any) {
      console.error('Error assigning crop:', err);
      setError(err.response?.data?.error || 'Failed to assign crop');
    } finally {
      setProcessing(false);
    }
  };

  const handleOpenSuggestions = async () => {
    if (!cropId) return;
    try {
      setLoadingSuggestions(true);
      setError(null);
      setSuccessMessage(null);
      const res = await faceCropsAPI.getSimilarFaces(parseInt(cropId), {
        k: assignOptions.k,
        include_unidentified: true,
        embedding_model: assignOptions.embedding_model,
      });
      setSuggestions(res.neighbors);
      setShowSuggestModal(true);
    } catch (err: any) {
      console.error('Error fetching suggestions:', err);
      setError(err.response?.data?.error || 'Failed to fetch similar faces');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleAssignFromSuggestion = async (candidateCropId: number, confidence?: number) => {
    if (!cropId) return;
    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);
      const res = await faceCropsAPI.assignFromCandidate(parseInt(cropId), candidateCropId, confidence);
      if (res.assigned && res.student_name) {
        setSuccessMessage(`Assigned to ${res.student_name}${res.confidence ? ` (confidence: ${(res.confidence * 100).toFixed(1)}%)` : ''}`);
      } else {
        setError(res.message || 'Could not assign from selected candidate');
      }
      await loadData();
      setShowSuggestModal(false);
    } catch (err: any) {
      console.error('Error assigning from candidate:', err);
      setError(err.response?.data?.error || 'Failed to assign from selected candidate');
    } finally {
      setProcessing(false);
    }
  };

  const getImageUrl = (path: string) => {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getModelDisplayName = (modelName: string | null) => {
    if (!modelName) return 'Not generated';
    switch (modelName) {
      case 'arcface':
        return 'ArcFace (512D)';
      case 'facenet512':
        return 'FaceNet512 (512D)';
      default:
        return modelName;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !crop) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-danger mb-4">Error</h2>
          <p className="text-gray-300 mb-4">{error || 'Face crop not found'}</p>
          <button
            onClick={() => navigate(`/classes/${classId}/sessions/${sessionId}/images/${imageId}`)}
            className="text-primary hover:text-primary-light transition-colors"
          >
            ← Back to Image
          </button>
        </div>
      </div>
    );
  }

  if (!crop) {
    return null;
  }

  const breadcrumbItems = [
    { label: 'Classes', path: '/classes' },
    { label: crop.class_name, path: `/classes/${classId}` },
    { label: crop.session_name, path: `/classes/${classId}/sessions/${sessionId}` },
    { label: 'Image Details', path: `/classes/${classId}/sessions/${sessionId}/images/${imageId}` },
    { label: 'Face Crop Details' },
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate(`/classes/${classId}/sessions/${sessionId}/images/${imageId}`)}
        className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-medium">Back to Image</span>
      </button>

      <Breadcrumb items={breadcrumbItems} />

      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 p-4 bg-success/10 border border-success/20 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-success-light flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-success-light">{successMessage}</p>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-success-light hover:text-success">
            <XIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-danger-light flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-danger-light">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-danger-light hover:text-danger">
            <XIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Face Crop Display */}
        <Card>
          <h2 className="text-xl font-semibold text-white mb-4">Face Crop</h2>
          <div className="aspect-square bg-dark-bg rounded-lg overflow-hidden border border-dark-border mb-4">
            <img
              src={getImageUrl(crop.crop_image_path)}
              alt={`Face crop ${crop.id}`}
              className="w-full h-full object-contain"
            />
          </div>

          {/* Status Badge */}
          <div className="flex items-center justify-center">
            {crop.is_identified && crop.student_name ? (
              <Badge variant="success" className="text-sm">
                <CheckCircle className="w-4 h-4 mr-2" />
                Identified as {crop.student_name}
              </Badge>
            ) : (
              <Badge variant="warning" className="text-sm">
                <AlertCircle className="w-4 h-4 mr-2" />
                Unidentified
              </Badge>
            )}
          </div>
        </Card>

        {/* Crop Details */}
        <Card>
          <h2 className="text-xl font-semibold text-white mb-4">Details</h2>

          <div className="space-y-4">
            {/* Crop ID */}
            <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
              <Hash className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-400 mb-1">Crop ID</p>
                <p className="text-white font-medium">{crop.id}</p>
              </div>
            </div>

            {/* Student Assignment */}
            <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
              <User className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-400 mb-1">Assigned Student</p>
                {crop.student_name ? (
                  <div>
                    <p className="text-white font-medium">{crop.student_name}</p>
                    {crop.confidence_score !== null && (
                      <p className="text-xs text-gray-500 mt-1">
                        Confidence: {(crop.confidence_score * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 italic">Not assigned</p>
                )}
              </div>
            </div>

            {/* Image Reference */}
            <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
              <ImageIcon className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-400 mb-1">Source Image</p>
                <button
                  onClick={() =>
                    navigate(`/classes/${classId}/sessions/${sessionId}/images/${imageId}`)
                  }
                  className="text-primary hover:text-primary-light transition-colors text-sm font-medium"
                >
                  View Image #{crop.image_id}
                </button>
              </div>
            </div>

            {/* Coordinates */}
            {crop.coordinates_dict && (
              <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
                <Hash className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-400 mb-1">Coordinates</p>
                  <p className="text-white text-sm font-mono">
                    x: {crop.coordinates_dict.x}, y: {crop.coordinates_dict.y}, w:{' '}
                    {crop.coordinates_dict.width}, h: {crop.coordinates_dict.height}
                  </p>
                </div>
              </div>
            )}

            {/* Embedding Model */}
            <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
              <Sparkles className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-400 mb-1">Embedding Model</p>
                <p className="text-white font-medium">{getModelDisplayName(crop.embedding_model)}</p>
              </div>
            </div>

            {/* Embedding Vector */}
            {crop.embedding && crop.embedding.length > 0 && (
              <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
                <Hash className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-400 mb-2">Embedding Vector</p>
                  <div className="bg-dark-bg rounded p-3 font-mono text-xs">
                    {showFullEmbedding ? (
                      <div className="space-y-1">
                        <p className="text-gray-400 mb-2">
                          {crop.embedding.length} dimensions:
                        </p>
                        <div className="max-h-64 overflow-y-auto">
                          <p className="text-primary break-all">
                            [{crop.embedding.map(v => v.toFixed(6)).join(', ')}]
                          </p>
                        </div>
                        <button
                          onClick={() => setShowFullEmbedding(false)}
                          className="text-primary hover:text-primary-light text-xs mt-2"
                        >
                          Show less
                        </button>
                      </div>
                    ) : (
                      <div>
                        <p className="text-primary">
                          [{crop.embedding.slice(0, 10).map(v => v.toFixed(6)).join(', ')}, ...]
                        </p>
                        <button
                          onClick={() => setShowFullEmbedding(true)}
                          className="text-primary hover:text-primary-light text-xs mt-2"
                        >
                          Show full vector ({crop.embedding.length} dimensions)
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Created Date */}
            <div className="flex items-start gap-3 p-3 bg-dark-hover rounded-lg">
              <Calendar className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-400 mb-1">Created</p>
                <p className="text-white text-sm">{formatDate(crop.created_at)}</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Buttons */}
      <Card className="mt-6">
        <h2 className="text-xl font-semibold text-white mb-4">Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Button
            onClick={() => setShowEmbeddingModal(true)}
            disabled={processing}
            className="w-full"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Embedding
          </Button>
          <Button
            onClick={() => setShowAssignModal(true)}
            disabled={processing}
            variant="secondary"
            className="w-full"
          >
            <UserCheck className="w-4 h-4 mr-2" />
            Assign to Student
          </Button>
          <Button
            onClick={handleOpenSuggestions}
            disabled={processing || !crop?.embedding_model}
            variant="secondary"
            className="w-full"
          >
            <UserCheck className="w-4 h-4 mr-2" />
            Suggest and Choose
          </Button>
        </div>
      </Card>

      {/* Generate Embedding Modal */}
      <Modal
        isOpen={showEmbeddingModal}
        onClose={() => setShowEmbeddingModal(false)}
        title="Generate Face Embedding"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Select an embedding model to generate a face embedding vector for this crop.
          </p>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Embedding Model
            </label>
            <div className="space-y-2">
              <button
                onClick={() => setSelectedModel('arcface')}
                className={`w-full p-4 rounded-lg border transition-colors text-left ${
                  selectedModel === 'arcface'
                    ? 'border-primary bg-primary/10'
                    : 'border-dark-border hover:border-gray-600 bg-dark-hover'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-white font-medium">ArcFace (512D)</p>
                  {selectedModel === 'arcface' && (
                    <CheckCircle className="w-5 h-5 text-primary" />
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  Higher accuracy, more detailed embeddings. Better for large datasets.
                </p>
              </button>
              <button
                onClick={() => setSelectedModel('facenet512')}
                className={`w-full p-4 rounded-lg border transition-colors text-left ${
                  selectedModel === 'facenet512'
                    ? 'border-primary bg-primary/10'
                    : 'border-dark-border hover:border-gray-600 bg-dark-hover'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-white font-medium">FaceNet512 (512D)</p>
                  {selectedModel === 'facenet512' && (
                    <CheckCircle className="w-5 h-5 text-primary" />
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  High-dimensional FaceNet variant. Balance between speed and accuracy.
                </p>
              </button>
            </div>
          </div>

          {/* Existing Embedding Warning */}
          {crop.embedding_model && (
            <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-warning">
                    This crop already has an embedding ({getModelDisplayName(crop.embedding_model)}). 
                    Generating a new embedding will replace the existing one.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowEmbeddingModal(false)}
              className="flex-1"
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleGenerateEmbedding}
              disabled={processing}
              className="flex-1"
            >
              {processing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate
                </>
              )}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Assign Crop Modal */}
      <Modal
        isOpen={showAssignModal}
        onClose={() => setShowAssignModal(false)}
        title="Assign Crop to Student"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            This will use K-Nearest Neighbors (KNN) to find the best matching student based on
            labeled face crops in the class.
          </p>

          {!crop.embedding_model && (
            <div className="p-3 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3">
              <XCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-danger-light">
                  This crop doesn't have an embedding yet. Please generate an embedding first.
                </p>
              </div>
            </div>
          )}

          {/* Configuration Options */}
          <div className="space-y-3">
            {/* K Value */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Number of Neighbors (K)
              </label>
              <input
                type="number"
                value={assignOptions.k}
                onChange={(e) =>
                  setAssignOptions({ ...assignOptions, k: parseInt(e.target.value) || 5 })
                }
                min={1}
                max={20}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 5</p>
            </div>

            {/* Similarity Threshold */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Similarity Threshold
              </label>
              <input
                type="number"
                value={assignOptions.similarity_threshold}
                onChange={(e) =>
                  setAssignOptions({
                    ...assignOptions,
                    similarity_threshold: parseFloat(e.target.value) || 0.6,
                  })
                }
                min={0}
                max={1}
                step={0.1}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
              />
              <p className="text-xs text-gray-500 mt-1">
                Minimum similarity score (0-1). Default: 0.6
              </p>
            </div>

            {/* Embedding Model */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Embedding Model
              </label>
              <select
                value={assignOptions.embedding_model}
                onChange={(e) =>
                  setAssignOptions({
                    ...assignOptions,
                    embedding_model: e.target.value as 'arcface' | 'facenet512',
                  })
                }
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
              >
                <option value="arcface">ArcFace (512D)</option>
                <option value="facenet512">FaceNet512 (512D)</option>
              </select>
            </div>

            {/* Use Voting */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="use-voting"
                checked={assignOptions.use_voting}
                onChange={(e) =>
                  setAssignOptions({ ...assignOptions, use_voting: e.target.checked })
                }
                className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
              />
              <label htmlFor="use-voting" className="text-sm text-gray-300 cursor-pointer">
                Use majority voting in KNN
              </label>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowAssignModal(false)}
              className="flex-1"
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAssignCrop}
              disabled={processing || !crop.embedding_model}
              className="flex-1"
            >
              {processing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Assigning...
                </>
              ) : (
                <>
                  <UserCheck className="w-4 h-4 mr-2" />
                  Assign
                </>
              )}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Suggestions Modal */}
      <Modal
        isOpen={showSuggestModal}
        onClose={() => setShowSuggestModal(false)}
        title={`Choose From Top-${assignOptions.k} Similar Faces`}
      >
        <div className="space-y-4">
          {!crop?.embedding_model && (
            <div className="p-3 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3">
              <XCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-danger-light">
                  This crop doesn't have an embedding yet. Please generate an embedding first.
                </p>
              </div>
            </div>
          )}

          {loadingSuggestions ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {suggestions.map((sug) => (
                <div key={sug.crop_id} className="p-3 bg-dark-hover rounded-lg border border-dark-border">
                  <div className="aspect-square rounded overflow-hidden mb-3 bg-dark-bg">
                    <img src={getImageUrl(sug.crop_image_path)} alt={`Candidate ${sug.crop_id}`} className="w-full h-full object-contain" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-white font-medium">
                      {sug.student_name || 'Unassigned'}
                    </p>
                    <p className="text-xs text-gray-400">Similarity: {(sug.similarity * 100).toFixed(1)}%</p>
                  </div>
                  <div className="mt-3">
                    {sug.student_id ? (
                      <Button
                        className="w-full"
                        onClick={() => handleAssignFromSuggestion(sug.crop_id, sug.similarity)}
                        disabled={processing}
                      >
                        Assign to {sug.student_name}
                      </Button>
                    ) : (
                      <Button className="w-full" variant="secondary" disabled>
                        No student assigned
                      </Button>
                    )}
                  </div>
                </div>
              ))}
              {suggestions.length === 0 && (
                <p className="text-gray-400 text-sm">No similar faces found.</p>
              )}
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button variant="secondary" onClick={() => setShowSuggestModal(false)} className="flex-1">
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default FaceCropDetailPage;
