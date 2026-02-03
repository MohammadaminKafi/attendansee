import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { studentsAPI, faceCropsAPI } from '@/services/api';
import { 
  SimilarFacesResponse, 
  SimilarFaceCrop, 
  StudentMergeSuggestion, 
  NoEmbeddingCrop,
} from '@/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import {
  ArrowLeft,
  UserCheck,
  UserPlus,
  AlertCircle,
  CheckCircle,
  X as XIcon,
  GitMerge,
  RefreshCw,
  User,
  Users,
  Layers,
} from 'lucide-react';

const TOP_K_OPTIONS = [5, 10, 20, 30];

const StudentSimilarFacesPage: React.FC = () => {
  const { classId, studentId } = useParams<{ classId: string; studentId: string }>();
  const navigate = useNavigate();

  // Data states
  const [data, setData] = useState<SimilarFacesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filter states
  const [kUnidentified, setKUnidentified] = useState(10);
  const [kIdentified, setKIdentified] = useState(10);
  const [includeNoEmbeddings, setIncludeNoEmbeddings] = useState(true);

  // Processing states
  const [assigningCropId, setAssigningCropId] = useState<number | null>(null);

  // Merge modal state
  const [showMergeModal, setShowMergeModal] = useState(false);
  const [selectedMergeStudent, setSelectedMergeStudent] = useState<StudentMergeSuggestion | null>(null);
  const [merging, setMerging] = useState(false);

  // Get image URL
  const getImageUrl = (path: string | null) => {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  };

  // Load data
  const loadData = useCallback(async () => {
    if (!studentId) return;

    try {
      setLoading(true);
      setError(null);

      const result = await studentsAPI.getSimilarFaces(parseInt(studentId), {
        k_unidentified: kUnidentified,
        k_identified: kIdentified,
        include_no_embeddings: includeNoEmbeddings,
        limit_no_embeddings: 50,
      });

      setData(result);
    } catch (err: any) {
      console.error('Error loading similar faces:', err);
      setError(err.response?.data?.error || 'Failed to load similar faces');
    } finally {
      setLoading(false);
    }
  }, [studentId, kUnidentified, kIdentified, includeNoEmbeddings]);

  // Load data on mount and when parameters change
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Assign unidentified face to current student
  const handleAssignToStudent = async (crop: SimilarFaceCrop | NoEmbeddingCrop) => {
    if (!studentId) return;

    try {
      setAssigningCropId(crop.crop_id);
      setError(null);

      await faceCropsAPI.assignToStudent(crop.crop_id, parseInt(studentId), 
        'similarity' in crop ? crop.similarity : undefined
      );

      setSuccessMessage(`Face assigned to ${data?.student.full_name}`);
      
      // Reload data to refresh the lists
      await loadData();
    } catch (err: any) {
      console.error('Error assigning face:', err);
      setError(err.response?.data?.error || 'Failed to assign face');
    } finally {
      setAssigningCropId(null);
    }
  };

  // Open merge confirmation modal
  const handleOpenMergeModal = (suggestion: StudentMergeSuggestion) => {
    setSelectedMergeStudent(suggestion);
    setShowMergeModal(true);
  };

  // Merge students
  const handleMerge = async () => {
    if (!studentId || !selectedMergeStudent) return;

    try {
      setMerging(true);
      setError(null);

      // Merge the other student INTO the current student
      // This means the current student will keep their identity and get the other student's face crops
      await studentsAPI.mergeStudents(selectedMergeStudent.student_id, {
        target_student_id: parseInt(studentId),
      });

      setSuccessMessage(
        `Successfully merged "${selectedMergeStudent.student_name}" into "${data?.student.full_name}". ` +
        `${selectedMergeStudent.matching_crops_count} matching crops transferred.`
      );
      setShowMergeModal(false);
      setSelectedMergeStudent(null);

      // Reload data
      await loadData();
    } catch (err: any) {
      console.error('Error merging students:', err);
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to merge students');
    } finally {
      setMerging(false);
    }
  };

  // Build breadcrumb
  const buildBreadcrumbItems = () => {
    const items: { label: string; href?: string }[] = [
      { label: 'Classes', href: '/classes' },
    ];
    if (classId) {
      items.push({ label: 'Class', href: `/classes/${classId}` });
    }
    if (data?.student) {
      items.push({ label: data.student.full_name, href: `/classes/${classId}/students/${studentId}` });
    }
    items.push({ label: 'Similar Faces' });
    return items;
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-danger mb-4">Error</h2>
          <p className="text-gray-300 mb-4">{error || 'Student not found'}</p>
          <Button onClick={() => navigate(`/classes/${classId}`)}>← Back to Class</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg p-8">
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(`/classes/${classId}/students/${studentId}`)}
          className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Back to Student</span>
        </button>

        {/* Breadcrumb */}
        <Breadcrumb items={buildBreadcrumbItems()} className="mb-6" />

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            {/* Student Profile Picture */}
            <div className="w-16 h-16 rounded-full overflow-hidden bg-dark-hover border-2 border-primary flex items-center justify-center">
              {data.student.profile_picture ? (
                <img
                  src={getImageUrl(data.student.profile_picture)}
                  alt={data.student.full_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <User className="w-8 h-8 text-gray-400" />
              )}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-100">Similar Faces</h1>
              <p className="text-gray-400">
                Finding faces similar to <span className="text-primary font-semibold">{data.student.full_name}</span>
                {data.student.student_id && <span className="text-gray-500"> ({data.student.student_id})</span>}
              </p>
            </div>
          </div>
        </div>

        {/* Filters Row */}
        <Card className="p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* K Unidentified */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Unidentified K:</span>
              <div className="flex gap-1">
                {TOP_K_OPTIONS.map((k) => (
                  <button
                    key={`unid-${k}`}
                    onClick={() => setKUnidentified(k)}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      kUnidentified === k
                        ? 'bg-primary text-white'
                        : 'bg-dark-bg text-gray-400 hover:bg-dark-hover hover:text-white'
                    }`}
                  >
                    {k}
                  </button>
                ))}
              </div>
            </div>

            {/* K Identified */}
            <div className="flex items-center gap-2 border-l border-dark-border pl-4">
              <span className="text-sm text-gray-400">Identified K:</span>
              <div className="flex gap-1">
                {TOP_K_OPTIONS.map((k) => (
                  <button
                    key={`id-${k}`}
                    onClick={() => setKIdentified(k)}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      kIdentified === k
                        ? 'bg-primary text-white'
                        : 'bg-dark-bg text-gray-400 hover:bg-dark-hover hover:text-white'
                    }`}
                  >
                    {k}
                  </button>
                ))}
              </div>
            </div>

            {/* Include No Embeddings */}
            <div className="flex items-center gap-2 border-l border-dark-border pl-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeNoEmbeddings}
                  onChange={(e) => setIncludeNoEmbeddings(e.target.checked)}
                  className="w-4 h-4 rounded border-dark-border bg-dark-bg text-primary focus:ring-primary"
                />
                <span className="text-sm text-gray-400">Show unembedded crops</span>
              </label>
            </div>

            {/* Refresh Button */}
            <Button
              variant="secondary"
              size="sm"
              onClick={loadData}
              disabled={loading}
              className="ml-auto"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
          </div>
        </Card>

        {/* Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <User className="w-4 h-4 text-primary" />
              <span className="text-xs text-gray-400">Student Crops</span>
            </div>
            <p className="text-2xl font-bold text-white">{data.stats.student_crops_count}</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <UserPlus className="w-4 h-4 text-success" />
              <span className="text-xs text-gray-400">Unidentified Similar</span>
            </div>
            <p className="text-2xl font-bold text-white">{data.stats.similar_unidentified_count}</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Users className="w-4 h-4 text-warning" />
              <span className="text-xs text-gray-400">Identified Similar</span>
            </div>
            <p className="text-2xl font-bold text-white">{data.stats.similar_identified_count}</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <GitMerge className="w-4 h-4 text-info" />
              <span className="text-xs text-gray-400">Merge Candidates</span>
            </div>
            <p className="text-2xl font-bold text-white">{data.stats.merge_candidates_count}</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Layers className="w-4 h-4 text-gray-400" />
              <span className="text-xs text-gray-400">No Embeddings</span>
            </div>
            <p className="text-2xl font-bold text-white">{data.stats.no_embedding_count}</p>
          </Card>
        </div>

        {/* Messages */}
        {successMessage && (
          <div className="mb-4 p-3 bg-success/10 border border-success/20 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-success" />
            <p className="text-sm text-success-light">{successMessage}</p>
            <button
              onClick={() => setSuccessMessage(null)}
              className="ml-auto text-success-light hover:text-success"
            >
              <XIcon className="w-4 h-4" />
            </button>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-danger" />
            <p className="text-sm text-danger-light">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-danger-light hover:text-danger"
            >
              <XIcon className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Student's Current Crops */}
        {data.student_crops.length > 0 && (
          <Card className="mb-6">
            <div className="bg-dark-hover p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                {data.student.full_name}'s Face Crops ({data.student_crops.length})
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                These are the faces assigned to this student, used to find similar faces.
              </p>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
                {data.student_crops.map((crop) => (
                  <div
                    key={crop.crop_id}
                    className="aspect-square rounded-lg overflow-hidden border-2 border-primary/30 bg-dark-bg"
                    title={`Session: ${crop.session_name}`}
                  >
                    <img
                      src={getImageUrl(crop.crop_image_path)}
                      alt={`Crop ${crop.crop_id}`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Similar Unidentified Faces - Can be assigned to this student */}
          <Card className="overflow-hidden">
            <div className="bg-dark-hover p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-success" />
                Similar Unidentified Faces
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                Unassigned faces that look similar. Click to assign to {data.student.full_name}.
              </p>
            </div>
            <div className="p-4 max-h-[60vh] overflow-y-auto">
              {data.similar_unidentified.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="w-10 h-10 text-gray-500 mx-auto mb-3" />
                  <p className="text-gray-400">No similar unidentified faces found</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {data.similar_unidentified.map((crop) => (
                    <div
                      key={crop.crop_id}
                      className="rounded-lg border border-dark-border bg-dark-card overflow-hidden"
                    >
                      <div className="aspect-square bg-dark-bg">
                        <img
                          src={getImageUrl(crop.crop_image_path)}
                          alt={`Crop ${crop.crop_id}`}
                          className="w-full h-full object-contain"
                        />
                      </div>
                      <div className="p-2 space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-400">Similarity:</span>
                          <span className="text-success font-medium">
                            {(crop.similarity * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 truncate" title={crop.session_name}>
                          {crop.session_name}
                        </p>
                        <Button
                          size="sm"
                          onClick={() => handleAssignToStudent(crop)}
                          disabled={assigningCropId !== null}
                          className="w-full text-xs py-1"
                        >
                          {assigningCropId === crop.crop_id ? (
                            'Assigning...'
                          ) : (
                            <>
                              <UserCheck className="w-3 h-3 mr-1" />
                              Assign
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>

          {/* Merge Suggestions - Students to merge */}
          <Card className="overflow-hidden">
            <div className="bg-dark-hover p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <GitMerge className="w-5 h-5 text-warning" />
                Merge Suggestions
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                Other students with similar faces. Merge to combine their face crops.
              </p>
            </div>
            <div className="p-4 max-h-[60vh] overflow-y-auto">
              {data.merge_suggestions.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-10 h-10 text-gray-500 mx-auto mb-3" />
                  <p className="text-gray-400">No similar students found for merging</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.merge_suggestions.map((suggestion) => (
                    <div
                      key={suggestion.student_id}
                      className="rounded-lg border border-dark-border bg-dark-card p-3"
                    >
                      <div className="flex items-start gap-3">
                        {/* Student Profile */}
                        <div className="w-12 h-12 rounded-full overflow-hidden bg-dark-bg flex-shrink-0 border border-dark-border">
                          {suggestion.profile_picture ? (
                            <img
                              src={getImageUrl(suggestion.profile_picture)}
                              alt={suggestion.student_name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-500">
                              <User className="w-6 h-6" />
                            </div>
                          )}
                        </div>

                        {/* Student Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-white truncate">
                            {suggestion.student_name}
                          </h4>
                          {suggestion.student_number && (
                            <p className="text-xs text-gray-400">ID: {suggestion.student_number}</p>
                          )}
                          <div className="flex gap-3 mt-1 text-xs">
                            <span className="text-gray-400">
                              Matches: <span className="text-warning">{suggestion.matching_crops_count}</span>
                            </span>
                            <span className="text-gray-400">
                              Max Sim: <span className="text-success">{(suggestion.max_similarity * 100).toFixed(0)}%</span>
                            </span>
                          </div>
                        </div>

                        {/* Merge Button */}
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleOpenMergeModal(suggestion)}
                          disabled={assigningCropId !== null}
                          className="flex-shrink-0"
                        >
                          <GitMerge className="w-4 h-4 mr-1" />
                          Merge
                        </Button>
                      </div>

                      {/* Matching Crops Preview */}
                      {suggestion.matching_crops.length > 0 && (
                        <div className="mt-3 flex gap-1 overflow-x-auto pb-1">
                          {suggestion.matching_crops.slice(0, 5).map((crop) => (
                            <div
                              key={crop.crop_id}
                              className="w-10 h-10 flex-shrink-0 rounded overflow-hidden border border-dark-border"
                              title={`Similarity: ${(crop.similarity * 100).toFixed(0)}%`}
                            >
                              <img
                                src={getImageUrl(crop.crop_image_path)}
                                alt={`Match ${crop.crop_id}`}
                                className="w-full h-full object-cover"
                              />
                            </div>
                          ))}
                          {suggestion.matching_crops_count > 5 && (
                            <div className="w-10 h-10 flex-shrink-0 rounded bg-dark-bg border border-dark-border flex items-center justify-center text-xs text-gray-400">
                              +{suggestion.matching_crops_count - 5}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Face Crops Without Embeddings */}
        {includeNoEmbeddings && data.no_embedding_crops.length > 0 && (
          <Card className="mt-6">
            <div className="bg-dark-hover p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-gray-400" />
                Face Crops Without Embeddings ({data.no_embedding_crops.length})
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                These faces don't have embeddings yet. You can still manually assign them.
              </p>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
                {data.no_embedding_crops.map((crop) => (
                  <div
                    key={crop.crop_id}
                    className="rounded-lg border border-dark-border bg-dark-card overflow-hidden"
                  >
                    <div className="aspect-square bg-dark-bg">
                      <img
                        src={getImageUrl(crop.crop_image_path)}
                        alt={`Crop ${crop.crop_id}`}
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <div className="p-2 space-y-1">
                      <p className="text-xs text-gray-500 truncate" title={crop.session_name}>
                        {crop.session_name}
                      </p>
                      {crop.is_identified ? (
                        <p className="text-xs text-warning truncate">
                          {crop.student_name}
                        </p>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleAssignToStudent(crop)}
                          disabled={assigningCropId !== null}
                          className="w-full text-xs py-1"
                        >
                          {assigningCropId === crop.crop_id ? '...' : 'Assign'}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Merge Confirmation Modal */}
        <Modal
          isOpen={showMergeModal}
          onClose={() => {
            setShowMergeModal(false);
            setSelectedMergeStudent(null);
          }}
          title="Merge Students"
          className="max-w-lg"
        >
          {selectedMergeStudent && (
            <div className="space-y-4">
              <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
                <p className="text-sm text-warning-light">
                  <strong>Warning:</strong> This action will merge{' '}
                  <span className="font-semibold">{selectedMergeStudent.student_name}</span> into{' '}
                  <span className="font-semibold">{data?.student.full_name}</span>.
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-gray-300">This will:</p>
                <ul className="list-disc list-inside text-sm text-gray-400 space-y-1">
                  <li>Transfer all face crops from "{selectedMergeStudent.student_name}" to "{data?.student.full_name}"</li>
                  <li>Delete the student "{selectedMergeStudent.student_name}"</li>
                  <li>Keep all data associated with "{data?.student.full_name}"</li>
                </ul>
              </div>

              <div className="flex items-center justify-center gap-4 p-4 bg-dark-bg rounded-lg">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-full overflow-hidden bg-dark-border mx-auto mb-2">
                    {selectedMergeStudent.profile_picture ? (
                      <img
                        src={getImageUrl(selectedMergeStudent.profile_picture)}
                        alt={selectedMergeStudent.student_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-500">
                        <User className="w-8 h-8" />
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-white">{selectedMergeStudent.student_name}</p>
                  <p className="text-xs text-gray-400">{selectedMergeStudent.matching_crops_count} crops</p>
                </div>

                <ArrowLeft className="w-8 h-8 text-primary rotate-180" />

                <div className="text-center">
                  <div className="w-16 h-16 rounded-full overflow-hidden bg-dark-border mx-auto mb-2 border-2 border-primary">
                    {data?.student.profile_picture ? (
                      <img
                        src={getImageUrl(data.student.profile_picture)}
                        alt={data.student.full_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-500">
                        <User className="w-8 h-8" />
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-white">{data?.student.full_name}</p>
                  <p className="text-xs text-primary">Target</p>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowMergeModal(false);
                    setSelectedMergeStudent(null);
                  }}
                  className="flex-1"
                  disabled={merging}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleMerge}
                  className="flex-1 bg-warning hover:bg-warning/80"
                  disabled={merging}
                >
                  {merging ? 'Merging...' : 'Confirm Merge'}
                </Button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </div>
  );
};

export default StudentSimilarFacesPage;
