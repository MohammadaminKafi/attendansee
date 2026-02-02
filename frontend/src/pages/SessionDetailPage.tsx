import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { sessionsAPI, imagesAPI, classesAPI, studentsAPI, faceCropsAPI } from '@/services/api';
import { Session, Image, Class, FaceCropDetail, Student, AutoAssignAllCropsResponse, ManualAttendance } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ProcessingOverlay } from '@/components/ui/ProcessingSpinner';
import { FaceCropsSection } from '@/components/ui/FaceCropsSection';
import { 
  EmbeddingGenerationModal, 
  EmbeddingGenerationOptions, 
  ClusteringModal, 
  ClusteringOptions,
  AutoAssignModal,
  AutoAssignOptions,
  AutoAssignResultModal,
  ActionsMenu,
  ConfirmationModal,
} from '@/components/ui';
import { Upload, Trash2, Clock, CheckCircle, XCircle, ArrowLeft, Play, Layers, Sparkles, Users, UserCog, Hand, RotateCcw, Wand2 } from 'lucide-react';

const SessionDetailPage: React.FC = () => {
  const { classId, sessionId } = useParams<{ classId: string; sessionId: string }>();
  const navigate = useNavigate();
  
  const [session, setSession] = useState<Session | null>(null);
  const [classData, setClassData] = useState<Class | null>(null);
  const [images, setImages] = useState<Image[]>([]);
  const [faceCrops, setFaceCrops] = useState<FaceCropDetail[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteImageModal, setShowDeleteImageModal] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState<number | null>(null);
  const [showFaceCropsSection, setShowFaceCropsSection] = useState(false);
  
  // Processing states
  const [processingImages, setProcessingImages] = useState<Set<number>>(new Set());
  const [processingAll, setProcessingAll] = useState(false);
  const [processProgress, setProcessProgress] = useState({ current: 0, total: 0 });

  // Embedding generation states
  const [showEmbeddingModal, setShowEmbeddingModal] = useState(false);
  const [generatingEmbeddings, setGeneratingEmbeddings] = useState(false);
  const [embeddingProgressText, setEmbeddingProgressText] = useState<string | null>(null);
  const [embeddingProgress, setEmbeddingProgress] = useState<{current: number; total: number}>({ current: 0, total: 0 });

  // Clustering states
  const [showClusteringModal, setShowClusteringModal] = useState(false);
  const [clusteringInProgress, setClusteringInProgress] = useState(false);
  const [clusteringResult, setClusteringResult] = useState<any>(null);
  const [showClusteringResultModal, setShowClusteringResultModal] = useState(false);

  // Auto-assign states
  const [showAutoAssignModal, setShowAutoAssignModal] = useState(false);
  const [autoAssignInProgress, setAutoAssignInProgress] = useState(false);
  const [autoAssignResult, setAutoAssignResult] = useState<AutoAssignAllCropsResponse | null>(null);
  const [showAutoAssignResultModal, setShowAutoAssignResultModal] = useState(false);

  // Manual attendance states
  const [showManualAttendanceModal, setShowManualAttendanceModal] = useState(false);
  const [manualAttendanceRecords, setManualAttendanceRecords] = useState<ManualAttendance[]>([]);
  const [loadingManualAttendance, setLoadingManualAttendance] = useState(false);

  // Management action states
  const [showClearSessionModal, setShowClearSessionModal] = useState(false);
  const [showResetSessionModal, setShowResetSessionModal] = useState(false);
  const [showUnassignAllModal, setShowUnassignAllModal] = useState(false);
  const [managementProcessing, setManagementProcessing] = useState(false);

  useEffect(() => {
    loadData();
  }, [classId, sessionId]);

  const loadData = async () => {
    if (!classId || !sessionId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const [sessionData, classInfo, imagesData, studentsData, faceCropsResponse] = await Promise.all([
        sessionsAPI.getSession(parseInt(sessionId)),
        classesAPI.getClass(parseInt(classId)),
        imagesAPI.getImages(parseInt(sessionId)),
        studentsAPI.getStudents(parseInt(classId)),
        sessionsAPI.getSessionFaceCrops(parseInt(sessionId))
      ]);
      
      setSession(sessionData);
      setClassData(classInfo);
      setImages(imagesData);
      setStudents(studentsData);
      setFaceCrops(faceCropsResponse.face_crops);
      
      // Show face crops section if there are any crops
      if (faceCropsResponse.face_crops.length > 0) {
        setShowFaceCropsSection(true);
      }

      // Load manual attendance records
      try {
        const manualAttendanceData = await sessionsAPI.getManualAttendance(parseInt(sessionId));
        setManualAttendanceRecords(manualAttendanceData.manual_attendance);
      } catch (err) {
        // Ignore if it fails, manual attendance is optional
        console.log('Manual attendance not loaded:', err);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load session data');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !sessionId) return;

    // Check image limit
    if (images.length >= 20) {
      setError('Maximum 20 images per session');
      return;
    }

    const remainingSlots = 20 - images.length;
    const filesToUpload = Array.from(files).slice(0, remainingSlots);

    setUploading(true);
    setError(null);

    try {
      // Upload files sequentially to avoid overwhelming the server
      for (const file of filesToUpload) {
        const newImage = await imagesAPI.uploadImage(parseInt(sessionId), file);
        setImages(prev => [newImage, ...prev]);
      }
      
      if (files.length > remainingSlots) {
        setError(`Only ${remainingSlots} images uploaded. Maximum 20 images per session.`);
      }
    } catch (err) {
      console.error('Error uploading image:', err);
      setError('Failed to upload one or more images');
    } finally {
      setUploading(false);
      // Reset the file input
      e.target.value = '';
    }
  };

  const openDeleteImageModal = (imageId: number) => {
    setDeletingImageId(imageId);
    setShowDeleteImageModal(true);
  };

  const handleDelete = async () => {
    if (!deletingImageId) return;

    try {
      await imagesAPI.deleteImage(deletingImageId);
      setImages(prev => prev.filter(img => img.id !== deletingImageId));
      setShowDeleteImageModal(false);
      setDeletingImageId(null);
    } catch (err) {
      console.error('Error deleting image:', err);
      setError('Failed to delete image');
      setShowDeleteImageModal(false);
      setDeletingImageId(null);
    }
  };

  const handleProcessImage = async (imageId: number) => {
    try {
      setProcessingImages(prev => new Set(prev).add(imageId));
      setError(null);

      await imagesAPI.processImage(imageId, {
        detector_backend: 'retinaface',
        confidence_threshold: 0.5,
        apply_background_effect: true,
      });

      // Reload the specific image
      const updatedImage = await imagesAPI.getImage(imageId);
      setImages(prev => prev.map(img => img.id === imageId ? updatedImage : img));
      
      // Reload session to update statistics
      if (sessionId) {
        const updatedSession = await sessionsAPI.getSession(parseInt(sessionId));
        setSession(updatedSession);
      }
    } catch (err: any) {
      console.error('Error processing image:', err);
      setError(err.response?.data?.error || 'Failed to process image');
    } finally {
      setProcessingImages(prev => {
        const next = new Set(prev);
        next.delete(imageId);
        return next;
      });
    }
  };

  const handleProcessAllImages = async () => {
    const unprocessedImages = images.filter(img => !img.is_processed);
    
    if (unprocessedImages.length === 0) {
      setError('All images are already processed');
      return;
    }

    try {
      setProcessingAll(true);
      setError(null);
      setProcessProgress({ current: 0, total: unprocessedImages.length });

      // Process images sequentially to avoid overwhelming the server
      for (let i = 0; i < unprocessedImages.length; i++) {
        const img = unprocessedImages[i];
        setProcessProgress({ current: i, total: unprocessedImages.length });
        
        try {
          await imagesAPI.processImage(img.id, {
            detector_backend: 'retinaface',
            confidence_threshold: 0.5,
            apply_background_effect: true,
          });

          // Update the specific image in state
          const updatedImage = await imagesAPI.getImage(img.id);
          setImages(prev => prev.map(image => image.id === img.id ? updatedImage : image));
        } catch (err) {
          console.error(`Error processing image ${img.id}:`, err);
          // Continue with next image even if one fails
        }
      }

      setProcessProgress({ current: unprocessedImages.length, total: unprocessedImages.length });

      // Reload session to update statistics
      if (sessionId) {
        const updatedSession = await sessionsAPI.getSession(parseInt(sessionId));
        setSession(updatedSession);
      }
    } catch (err) {
      console.error('Error processing images:', err);
      setError('Failed to process some images');
    } finally {
      setProcessingAll(false);
      setProcessProgress({ current: 0, total: 0 });
    }
  };

  const loadManualAttendance = async () => {
    if (!sessionId) return;
    
    try {
      setLoadingManualAttendance(true);
      const response = await sessionsAPI.getManualAttendance(parseInt(sessionId));
      setManualAttendanceRecords(response.manual_attendance);
    } catch (err) {
      console.error('Error loading manual attendance:', err);
    } finally {
      setLoadingManualAttendance(false);
    }
  };

  const handleMarkAttendance = async (studentId: number, isPresent: boolean) => {
    if (!sessionId) return;
    
    try {
      await sessionsAPI.markAttendance(parseInt(sessionId), {
        student_id: studentId,
        is_present: isPresent,
      });
      
      // Reload manual attendance records
      await loadManualAttendance();
    } catch (err) {
      console.error('Error marking attendance:', err);
      setError('Failed to mark attendance');
    }
  };

  const handleUnmarkAttendance = async (studentId: number) => {
    if (!sessionId) return;
    
    try {
      await sessionsAPI.unmarkAttendance(parseInt(sessionId), studentId);
      
      // Reload manual attendance records
      await loadManualAttendance();
    } catch (err) {
      console.error('Error unmarking attendance:', err);
      setError('Failed to unmark attendance');
    }
  };

  const openManualAttendanceModal = () => {
    loadManualAttendance();
    setShowManualAttendanceModal(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getImageUrl = (path: string) => {
    if (!path) return '';
    // Backend now returns absolute URLs, use them directly
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    // Fallback for relative paths (shouldn't happen with updated serializer)
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    // Ensure path starts with /
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl}${normalizedPath}`;
  };

  const handleFaceCropsUpdate = async () => {
    if (!sessionId) return;
    try {
      const faceCropsResponse = await sessionsAPI.getSessionFaceCrops(parseInt(sessionId));
      setFaceCrops(faceCropsResponse.face_crops);
      
      // Also reload images to update face crop counts
      const imagesData = await imagesAPI.getImages(parseInt(sessionId));
      setImages(imagesData);
    } catch (err) {
      console.error('Failed to reload face crops:', err);
    }
  };

  const handleGenerateEmbeddings = async (options: EmbeddingGenerationOptions) => {
    if (!sessionId) return;

    try {
      setGeneratingEmbeddings(true);
      setShowEmbeddingModal(false); // Close modal immediately to show progress bar
      setError(null);

      // Determine which crops need embeddings
      const cropsToProcess = faceCrops.filter(c => !c.embedding_model).map(c => c.id);
      if (cropsToProcess.length === 0) {
        setEmbeddingProgressText('All face crops already have embeddings');
        setTimeout(() => setEmbeddingProgressText(null), 1500);
        return;
      }
      setEmbeddingProgress({ current: 0, total: cropsToProcess.length });

      let done = 0;
      for (const cropId of cropsToProcess) {
        try {
          await faceCropsAPI.generateEmbedding(cropId, options.model_name || 'arcface');
        } catch (e) {
          // continue on error
        } finally {
          done += 1;
          setEmbeddingProgress({ current: done, total: cropsToProcess.length });
        }
      }

      setEmbeddingProgressText(`Generated embeddings for ${done} / ${cropsToProcess.length} crops`);
      await handleFaceCropsUpdate();
      if (sessionId) {
        const updatedSession = await sessionsAPI.getSession(parseInt(sessionId));
        setSession(updatedSession);
      }
      setTimeout(() => {
        setEmbeddingProgressText(null);
        setEmbeddingProgress({ current: 0, total: 0 });
      }, 1500);
    } catch (err: any) {
      console.error('Error generating embeddings:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to generate embeddings';
      setError(errorMsg);
      setEmbeddingProgressText(null);
      setEmbeddingProgress({ current: 0, total: 0 });
    } finally {
      setGeneratingEmbeddings(false);
    }
  };

  const handleClusterCrops = async (options: ClusteringOptions) => {
    if (!sessionId) return;

    try {
      setClusteringInProgress(true);
      setError(null);
      setShowClusteringModal(false);

      const result = await sessionsAPI.clusterCrops(parseInt(sessionId), options);
      
      setClusteringResult(result);
      setShowClusteringResultModal(true);

      // Reload face crops and students
      await handleFaceCropsUpdate();
      if (classId) {
        const studentsData = await studentsAPI.getStudents(parseInt(classId));
        setStudents(studentsData);
      }
      if (sessionId) {
        const updatedSession = await sessionsAPI.getSession(parseInt(sessionId));
        setSession(updatedSession);
      }
    } catch (err: any) {
      console.error('Error clustering face crops:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to cluster face crops';
      setError(errorMsg);
    } finally {
      setClusteringInProgress(false);
    }
  };

  const handleAutoAssignAll = async (options: AutoAssignOptions) => {
    if (!sessionId) return;

    try {
      setAutoAssignInProgress(true);
      setError(null);
      setShowAutoAssignModal(false);

      const result = await sessionsAPI.autoAssignAllCrops(parseInt(sessionId), {
        k: options.k,
        similarity_threshold: options.similarity_threshold,
        embedding_model: options.embedding_model,
        use_voting: options.use_voting,
      });

      setAutoAssignResult(result);
      setShowAutoAssignResultModal(true);

      // Reload face crops to reflect assignments
      await handleFaceCropsUpdate();
      if (sessionId) {
        const updatedSession = await sessionsAPI.getSession(parseInt(sessionId));
        setSession(updatedSession);
      }
    } catch (err: any) {
      console.error('Error auto-assigning crops:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to auto-assign crops';
      setError(errorMsg);
    } finally {
      setAutoAssignInProgress(false);
    }
  };

  const handleOpenManualAssign = () => {
    if (!classId || !sessionId) return;
    // Navigate to the new manual assignment page with session context
    navigate(`/classes/${classId}/manual-assignment?session_id=${sessionId}&scope=session`);
  };

  // Management action handlers
  const handleClearSession = async () => {
    if (!sessionId) return;
    
    try {
      setManagementProcessing(true);
      setError(null);
      
      await sessionsAPI.clearSession(parseInt(sessionId));
      
      setShowClearSessionModal(false);
      
      // Reload data
      await loadData();
    } catch (err: any) {
      console.error('Error clearing session:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to clear session';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  const handleResetSession = async () => {
    if (!sessionId) return;
    
    try {
      setManagementProcessing(true);
      setError(null);
      
      await sessionsAPI.resetSession(parseInt(sessionId));
      
      setShowResetSessionModal(false);
      
      // Reload data
      await loadData();
    } catch (err: any) {
      console.error('Error resetting session:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to reset session';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  const handleUnassignAll = async () => {
    if (!sessionId) return;
    
    try {
      setManagementProcessing(true);
      setError(null);
      
      await sessionsAPI.unassignAll(parseInt(sessionId));
      
      setShowUnassignAllModal(false);
      
      // Reload data
      await loadData();
    } catch (err: any) {
      console.error('Error unassigning face crops:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to unassign face crops';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!session || !classData) {
    return (
      <div className="p-8">
        <p className="text-danger">Session not found</p>
      </div>
    );
  }

  const breadcrumbItems = [
    { label: 'Classes', path: '/classes' },
    { label: classData.name, path: `/classes/${classId}` },
    { label: session.name }
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Processing Overlay */}
      <ProcessingOverlay 
        isProcessing={processingAll} 
        message="Processing images..." 
        progress={processProgress.total > 0 ? processProgress : undefined}
      />

      {/* Back Button */}
      <button
        onClick={() => navigate(`/classes/${classId}`)}
        className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-medium">Back to Class</span>
      </button>

      <Breadcrumb items={breadcrumbItems} className="mb-6" />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-100 mb-2">{session.name}</h1>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>Date: {new Date(session.date).toLocaleDateString()}</span>
              {session.start_time && <span>Start: {session.start_time}</span>}
              {session.end_time && <span>End: {session.end_time}</span>}
            </div>
          </div>
          <Badge variant={session.is_processed ? 'success' : 'warning'}>
            {session.is_processed ? 'Processed' : 'Pending'}
          </Badge>
        </div>
        
        {session.notes && (
          <div className="mt-4 p-4 bg-dark-card rounded-lg border border-dark-border">
            <p className="text-sm text-gray-300">{session.notes}</p>
          </div>
        )}
      </div>

      {/* Session-level Actions */}
      <div className="mb-6">
        <ActionsMenu
          categories={[
            {
              label: 'AI Actions',
              items: [
                {
                  id: 'process-images',
                  label: 'Process All Images',
                  description: `Detect and extract faces from all images. ${
                    images.filter(img => !img.is_processed).length > 0
                      ? `${images.filter(img => !img.is_processed).length} unprocessed image${
                          images.filter(img => !img.is_processed).length !== 1 ? 's' : ''
                        }`
                      : 'All images processed'
                  }`,
                  icon: <Layers className="w-5 h-5" />,
                  onClick: handleProcessAllImages,
                  disabled: processingAll || images.filter(img => !img.is_processed).length === 0,
                  isProcessing: processingAll,
                },
                {
                  id: 'generate-embeddings',
                  label: 'Generate Embeddings',
                  description: `Generate face embeddings for recognition. ${
                    faceCrops.filter(c => !c.embedding_model).length
                  } of ${faceCrops.length} face${faceCrops.length !== 1 ? 's' : ''} need embedding${
                    faceCrops.filter(c => !c.embedding_model).length !== 1 ? 's' : ''
                  }`,
                  icon: <Sparkles className="w-5 h-5" />,
                  onClick: () => setShowEmbeddingModal(true),
                  disabled: generatingEmbeddings || faceCrops.length === 0,
                  isProcessing: generatingEmbeddings,
                },
                {
                  id: 'auto-assign',
                  label: 'Identify All Students',
                  description: 'Automatically identify and assign all unidentified faces to students',
                  icon: <Wand2 className="w-5 h-5" />,
                  onClick: () => setShowAutoAssignModal(true),
                  disabled: autoAssignInProgress || faceCrops.filter(c => !c.is_identified && c.embedding_model).length === 0,
                  isProcessing: autoAssignInProgress,
                },
                {
                  id: 'cluster-faces',
                  label: 'Group Student Faces',
                  description: 'Automatically cluster similar faces together to create student profiles',
                  icon: <Users className="w-5 h-5" />,
                  onClick: () => setShowClusteringModal(true),
                  disabled: clusteringInProgress || faceCrops.length === 0,
                  isProcessing: clusteringInProgress,
                },
              ],
            },
            {
              label: 'Manual Actions',
              items: [
                {
                  id: 'manual-assignment',
                  label: 'Assign Student Face',
                  description: 'Manually review and assign unidentified faces to students',
                  icon: <UserCog className="w-5 h-5" />,
                  onClick: handleOpenManualAssign,
                  disabled: faceCrops.filter(c => !c.is_identified && c.embedding_model).length === 0,
                  isProcessing: false,
                },
                {
                  id: 'manual-attendance',
                  label: 'Mark Manual Attendance',
                  description: 'Manually mark students as present or absent in this session',
                  icon: <Hand className="w-5 h-5" />,
                  onClick: openManualAttendanceModal,
                  disabled: loadingManualAttendance || students.length === 0,
                  isProcessing: loadingManualAttendance,
                },
              ],
            },
            {
              label: 'Management',
              items: [
                {
                  id: 'unassign-all',
                  label: 'Unassign All Faces',
                  description: 'Remove all student assignments from face crops in this session',
                  icon: <RotateCcw className="w-5 h-5" />,
                  onClick: () => setShowUnassignAllModal(true),
                  disabled: managementProcessing || faceCrops.filter(c => c.is_identified).length === 0,
                  isProcessing: false,
                },
                {
                  id: 'reset-session',
                  label: 'Reset Session',
                  description: 'Remove all processing results while keeping original images',
                  icon: <RotateCcw className="w-5 h-5" />,
                  onClick: () => setShowResetSessionModal(true),
                  disabled: managementProcessing || images.length === 0,
                  isProcessing: false,
                },
                {
                  id: 'clear-session',
                  label: 'Clear All Session Data',
                  description: 'Delete all images, face crops, and attendance records',
                  icon: <Trash2 className="w-5 h-5" />,
                  onClick: () => setShowClearSessionModal(true),
                  disabled: managementProcessing,
                  isProcessing: false,
                },
              ],
            },
          ]}
        />
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-dark-card rounded-lg border border-dark-border hover:border-primary transition-colors">
          <p className="text-sm text-gray-400">Images</p>
          <p className="text-2xl font-bold text-white">{images.length}</p>
        </div>
        <div className="p-4 bg-dark-card rounded-lg border border-dark-border hover:border-primary transition-colors">
          <p className="text-sm text-gray-400">Total Faces</p>
          <p className="text-2xl font-bold text-white">{session.total_faces_count}</p>
        </div>
        <div className="p-4 bg-dark-card rounded-lg border border-dark-border hover:border-primary transition-colors">
          <p className="text-sm text-gray-400">Identified</p>
          <p className="text-2xl font-bold text-white">{session.identified_faces_count}</p>
        </div>
      </div>

      {/* Upload Section */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Images</h2>
            <p className="text-sm text-gray-400 mt-1">
              {images.length} / 20 images uploaded • {images.filter(img => img.is_processed).length} processed
            </p>
          </div>
          <label className={`inline-flex items-center justify-center btn-primary px-4 py-2 ${uploading || images.length >= 20 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              disabled={uploading || images.length >= 20}
              className="hidden"
            />
            <Upload className="w-4 h-4 mr-2" />
            {uploading ? 'Uploading...' : 'Upload Images'}
          </label>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg">
            <p className="text-sm text-danger-light">{error}</p>
          </div>
        )}

        {images.length >= 20 && (
          <div className="mb-4 p-3 bg-warning/10 border border-warning/20 rounded-lg">
            <p className="text-sm text-warning-light">
              Maximum image limit reached (20 images)
            </p>
          </div>
        )}

        {/* Images Grid */}
        {images.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-dark-border rounded-lg">
            <Upload className="w-12 h-12 text-gray-500 mx-auto mb-3" />
            <p className="text-gray-400 mb-2">No images uploaded yet</p>
            <p className="text-sm text-gray-500">Upload images to start processing</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {images.map((image) => (
              <div
                key={image.id}
                className="relative group bg-dark-card rounded-lg overflow-hidden border border-dark-border hover:border-primary transition-colors"
              >
                {/* Image Preview - Clickable */}
                <div 
                  className="aspect-square bg-dark-bg flex items-center justify-center cursor-pointer"
                  onClick={() => navigate(`/classes/${classId}/sessions/${sessionId}/images/${image.id}`)}
                >
                  <img
                    src={getImageUrl(image.original_image_path)}
                    alt={`Upload ${image.id}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23334155" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23cbd5e1" font-family="sans-serif" font-size="14"%3ENo Preview%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </div>

                {/* Image Info Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  <div className="absolute bottom-0 left-0 right-0 p-3 pointer-events-auto">
                    <div className="flex items-center gap-2 mb-2">
                      {image.is_processed ? (
                        <Badge variant="success" className="text-xs">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Processed
                        </Badge>
                      ) : (
                        <Badge variant="warning" className="text-xs">
                          <XCircle className="w-3 h-3 mr-1" />
                          Pending
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      {!image.is_processed && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleProcessImage(image.id);
                          }}
                          disabled={processingImages.has(image.id)}
                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-primary hover:bg-primary-dark rounded text-white text-xs transition-colors disabled:opacity-50"
                        >
                          {processingImages.has(image.id) ? (
                            <>Processing...</>
                          ) : (
                            <>
                              <Play className="w-3 h-3" />
                              Process
                            </>
                          )}
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openDeleteImageModal(image.id);
                        }}
                        className="p-1.5 bg-danger hover:bg-danger-dark rounded text-white transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center text-xs text-gray-300">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDate(image.upload_date)}
                    </div>
                    {image.face_crop_count > 0 && (
                      <div className="text-xs text-gray-400 mt-1">
                        {image.face_crop_count} face{image.face_crop_count !== 1 ? 's' : ''} detected
                      </div>
                    )}
                  </div>
                </div>

                {/* Status Badge (Always Visible) */}
                <div className="absolute top-2 right-2">
                  {image.is_processed ? (
                    <div className="w-2 h-2 rounded-full bg-success"></div>
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-warning animate-pulse"></div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Face Crops Section */}
      {showFaceCropsSection && (
        <Card className="mt-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-white">Session Face Crops</h2>
            <p className="text-sm text-gray-400 mt-1">
              All detected faces across {images.length} image{images.length !== 1 ? 's' : ''} • {faceCrops.filter(c => !c.embedding_model).length} / {faceCrops.length} need embeddings
            </p>
          </div>
          <FaceCropsSection
            faceCrops={faceCrops}
            students={students}
            onUpdate={handleFaceCropsUpdate}
            title=""
            description=""
            showImageInfo={true}
            classId={classId ? parseInt(classId) : undefined}
          />
        </Card>
      )}

      {/* Embedding Generation Progress */}
      {(generatingEmbeddings || embeddingProgressText) && (
        <ProcessingOverlay 
          isProcessing={true} 
          message={embeddingProgressText || 'Generating embeddings...'} 
          progress={embeddingProgress.total > 0 ? embeddingProgress : undefined}
        />
      )}

      {/* Embedding Generation Modal */}
      <EmbeddingGenerationModal
        isOpen={showEmbeddingModal}
        onClose={() => setShowEmbeddingModal(false)}
        onGenerate={handleGenerateEmbeddings}
        isProcessing={generatingEmbeddings}
        unprocessedImagesCount={images.filter(img => !img.is_processed).length}
        title="Generate Session Embeddings"
        description="Generate embeddings for all face crops in this session to enable face recognition and matching."
      />

      {/* Clustering Progress */}
      {clusteringInProgress && (
        <ProcessingOverlay 
          isProcessing={true} 
          message="Clustering face crops..." 
        />
      )}

      {/* Clustering Modal */}
      <ClusteringModal
        isOpen={showClusteringModal}
        onClose={() => setShowClusteringModal(false)}
        onCluster={handleClusterCrops}
        isProcessing={clusteringInProgress}
        cropsWithoutEmbeddings={faceCrops.filter(c => !c.embedding_model).length}
        title="Cluster Face Crops"
        description="Automatically group similar face crops into clusters and create students for each cluster."
      />

      {/* Clustering Result Modal */}
      {clusteringResult && (
        <Modal
          isOpen={showClusteringResultModal}
          onClose={() => {
            setShowClusteringResultModal(false);
            setClusteringResult(null);
          }}
          title="Clustering Complete"
        >
          <div className="space-y-4">
            <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
              <p className="text-success font-medium mb-2">Successfully clustered face crops!</p>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-2 border-b border-dark-border">
                <span className="text-gray-400">Total Face Crops:</span>
                <span className="text-white font-medium">{clusteringResult.total_face_crops}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-dark-border">
                <span className="text-gray-400">Crops with Embeddings:</span>
                <span className="text-white font-medium">{clusteringResult.crops_with_embeddings}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-dark-border">
                <span className="text-gray-400">Clusters Created:</span>
                <span className="text-white font-medium">{clusteringResult.clusters_created}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-dark-border">
                <span className="text-gray-400">Students Created:</span>
                <span className="text-white font-medium">{clusteringResult.students_created}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-dark-border">
                <span className="text-gray-400">Crops Assigned:</span>
                <span className="text-white font-medium">{clusteringResult.crops_assigned}</span>
              </div>
              {clusteringResult.outliers > 0 && (
                <div className="flex justify-between py-2 border-b border-dark-border">
                  <span className="text-gray-400">Outliers (Unassigned):</span>
                  <span className="text-warning font-medium">{clusteringResult.outliers}</span>
                </div>
              )}
            </div>

            {clusteringResult.student_names && clusteringResult.student_names.length > 0 && (
              <div>
                <p className="text-sm text-gray-400 mb-2">Created Students:</p>
                <div className="max-h-40 overflow-y-auto space-y-1">
                  {clusteringResult.student_names.map((name: string, idx: number) => (
                    <div key={idx} className="text-sm text-white bg-dark-hover px-3 py-2 rounded">
                      {name}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowClusteringResultModal(false);
                  setClusteringResult(null);
                }}
                className="flex-1"
              >
                Close
              </Button>
              <Button
                onClick={() => {
                  setShowClusteringResultModal(false);
                  setClusteringResult(null);
                  if (classId) {
                    navigate(`/classes/${classId}`);
                  }
                }}
                className="flex-1"
              >
                View Class
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Auto-Assign Modal */}
      <AutoAssignModal
        isOpen={showAutoAssignModal}
        onClose={() => setShowAutoAssignModal(false)}
        onAutoAssign={handleAutoAssignAll}
        isProcessing={autoAssignInProgress}
        cropsWithoutEmbeddings={faceCrops.filter(c => !c.embedding_model).length}
        unidentifiedCropsCount={faceCrops.filter(c => !c.is_identified && c.embedding_model).length}
        title="Auto-Assign All Face Crops"
        description="Automatically assign all unidentified face crops in this session to students using similarity matching."
      />

      {/* Auto-Assign Result Modal */}
      {autoAssignResult && (
        <AutoAssignResultModal
          isOpen={showAutoAssignResultModal}
          onClose={() => {
            setShowAutoAssignResultModal(false);
            setAutoAssignResult(null);
          }}
          result={autoAssignResult}
        />
      )}

      {/* Delete Image Modal */}
      <Modal
        isOpen={showDeleteImageModal}
        onClose={() => setShowDeleteImageModal(false)}
        title="Delete Image"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete this image?
          </p>

          <div className="p-3 bg-warning bg-opacity-10 border border-warning rounded-lg">
            <p className="text-warning text-sm">
              This action cannot be undone. The image and all associated face crops will be permanently deleted.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowDeleteImageModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={handleDelete}
              className="flex-1"
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>

      {/* Manual Attendance Modal */}
      <Modal
        isOpen={showManualAttendanceModal}
        onClose={() => setShowManualAttendanceModal(false)}
        title="Manual Attendance"
      >
        <div className="space-y-4">
          {loadingManualAttendance ? (
            <div className="text-center py-8">
              <p className="text-gray-400">Loading...</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {students.map((student) => {
                const manualRecord = manualAttendanceRecords.find(r => r.student === student.id);
                const isMarkedPresent = manualRecord?.is_present;
                const isMarkedAbsent = manualRecord && !manualRecord.is_present;
                const isAuto = !manualRecord;
                
                return (
                  <div
                    key={student.id}
                    className="flex items-center justify-between p-3 bg-dark-hover rounded-lg hover:bg-dark-border transition-colors"
                  >
                    <div>
                      <p className="text-white font-medium">{student.full_name}</p>
                      {student.student_id && (
                        <p className="text-sm text-gray-500">{student.student_id}</p>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-1 border border-dark-border rounded-lg p-1">
                      <button
                        onClick={() => handleMarkAttendance(student.id, true)}
                        disabled={loadingManualAttendance}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          isMarkedPresent
                            ? 'bg-success text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Mark as Present"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleMarkAttendance(student.id, false)}
                        disabled={loadingManualAttendance}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          isMarkedAbsent
                            ? 'bg-danger text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Mark as Absent"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleUnmarkAttendance(student.id)}
                        disabled={loadingManualAttendance || isAuto}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          isAuto
                            ? 'bg-primary text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Auto (based on face detection)"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-dark-border">
            <Button
              variant="secondary"
              onClick={() => setShowManualAttendanceModal(false)}
            >
              Done
            </Button>
          </div>
        </div>
      </Modal>

      {/* Management Confirmation Modals */}
      <ConfirmationModal
        isOpen={showClearSessionModal}
        onClose={() => setShowClearSessionModal(false)}
        onConfirm={handleClearSession}
        title="Clear All Session Data?"
        message="This will permanently delete all images, face crops, and manual attendance records in this session. This action cannot be undone."
        confirmText="Clear All Data"
        isDestructive={true}
        isProcessing={managementProcessing}
      />

      <ConfirmationModal
        isOpen={showResetSessionModal}
        onClose={() => setShowResetSessionModal(false)}
        onConfirm={handleResetSession}
        title="Reset Session?"
        message="This will delete all face crops and reset processing status for all images. Original images will be kept but you'll need to reprocess them. This action cannot be undone."
        confirmText="Reset Session"
        isDestructive={true}
        isProcessing={managementProcessing}
      />

      <ConfirmationModal
        isOpen={showUnassignAllModal}
        onClose={() => setShowUnassignAllModal(false)}
        onConfirm={handleUnassignAll}
        title="Unassign All Faces?"
        message="This will remove all student assignments from face crops in this session. Face crops will be kept but will become unidentified. This action cannot be undone."
        confirmText="Unassign All"
        isDestructive={true}
        isProcessing={managementProcessing}
      />
    </div>
  );
};

export default SessionDetailPage;
