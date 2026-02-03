import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { classesAPI, sessionsAPI, imagesAPI, faceCropsAPI } from '@/services/api';
import { Class, Image as ImageType } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ProcessingOverlay } from '@/components/ui/ProcessingSpinner';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Tabs, Tab } from '@/components/ui/Tabs';
import { StatCard } from '@/components/ui/StatCard';
import { SessionsTab } from '@/components/tabs/SessionsTab';
import { StudentsTab } from '@/components/tabs/StudentsTab';
import { ReportTab } from '@/components/tabs/ReportTab';
import { NotesTab } from '@/components/tabs/NotesTab';
import { EmbeddingGenerationModal, EmbeddingGenerationOptions, ClusteringModal, ClusteringOptions, AutoAssignModal, AutoAssignResultModal, ActionsMenu, ConfirmationModal } from '@/components/ui';
import { Modal } from '@/components/ui/Modal';
import { ArrowLeft, Layers, Sparkles, Users, Wand2, UserCheck, Trash2, RotateCcw } from 'lucide-react';

export const ClassDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [classData, setClassData] = useState<Class | null>(null);
  const [statistics, setStatistics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('sessions');

  // Processing states
  const [processingImages, setProcessingImages] = useState(false);
  const [processProgress, setProcessProgress] = useState({ current: 0, total: 0 });

  // Embedding generation states
  const [showEmbeddingModal, setShowEmbeddingModal] = useState(false);
  const [generatingEmbeddings, setGeneratingEmbeddings] = useState(false);
  const [embeddingProgress, setEmbeddingProgress] = useState({ current: 0, total: 0 });

  // Clustering states
  const [showClusteringModal, setShowClusteringModal] = useState(false);
  const [clusteringInProgress, setClusteringInProgress] = useState(false);
  const [clusteringResult, setClusteringResult] = useState<any>(null);
  const [showClusteringResultModal, setShowClusteringResultModal] = useState(false);

  // Auto-assign states
  const [showAutoAssignModal, setShowAutoAssignModal] = useState(false);
  const [autoAssigning, setAutoAssigning] = useState(false);
  const [autoAssignResult, setAutoAssignResult] = useState<any>(null);
  const [showAutoAssignResultModal, setShowAutoAssignResultModal] = useState(false);

  // Management action states
  const [showClearClassModal, setShowClearClassModal] = useState(false);
  const [showResetSessionsModal, setShowResetSessionsModal] = useState(false);
  const [showClearStudentsModal, setShowClearStudentsModal] = useState(false);
  const [showResetStudentsModal, setShowResetStudentsModal] = useState(false);
  const [managementProcessing, setManagementProcessing] = useState(false);

  const tabs: Tab[] = [
    { id: 'sessions', label: 'Sessions', icon: '📅' },
    { id: 'students', label: 'Students', icon: '👥' },
    { id: 'report', label: 'Report', icon: '📊' },
    { id: 'notes', label: 'Notes', icon: '📝' },
  ];

  useEffect(() => {
    if (id) {
      loadClassData();
    } else {
      setError('Invalid class ID');
      setLoading(false);
    }
  }, [id]);

  const loadClassData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError('');
      const [classResponse, statsResponse] = await Promise.all([
        classesAPI.getClass(parseInt(id)),
        classesAPI.getClassStatistics(parseInt(id)),
      ]);
      setClassData(classResponse);
      setStatistics(statsResponse);
    } catch (err: any) {
      console.error('Failed to load class data:', err);
      setError(err.response?.data?.detail || 'Failed to load class data');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessAllImages = async () => {
    if (!id) return;

    try {
      setProcessingImages(true);
      setError('');

      // Load all sessions for the class
      const sessions = await sessionsAPI.getSessions(parseInt(id));
      // Load images for each session and collect unprocessed ones
      const allImages: ImageType[] = [] as any;
      for (const s of sessions) {
        const imgs = await imagesAPI.getImages(s.id);
        allImages.push(...imgs);
      }
      const unprocessed = allImages.filter(img => !img.is_processed);
      if (unprocessed.length === 0) {
        setError('No unprocessed images to process');
        return;
      }
      setProcessProgress({ current: 0, total: unprocessed.length });

      // Sequentially process images and update progress
      let processed = 0;
      for (const img of unprocessed) {
        try {
          await imagesAPI.processImage(img.id, {
            detector_backend: 'retinaface',
            confidence_threshold: 0.5,
            apply_background_effect: true,
          });
        } catch (e) {
          // continue on error
        } finally {
          processed += 1;
          setProcessProgress({ current: processed, total: unprocessed.length });
        }
      }

      await loadClassData();
      setTimeout(() => setProcessProgress({ current: 0, total: 0 }), 1500);
    } catch (err: any) {
      console.error('Error processing images:', err);
      const errorMsg = err.response?.data?.error || 'Failed to process images';
      setError(errorMsg);
      setProcessProgress({ current: 0, total: 0 });
    } finally {
      setProcessingImages(false);
    }
  };

  const handleGenerateEmbeddings = async (options: EmbeddingGenerationOptions) => {
    if (!id) return;

    try {
      setGeneratingEmbeddings(true);
      setShowEmbeddingModal(false); // Close modal immediately to show progress bar
      setError('');

      // Gather all crops without embeddings across the class
      const sessions = await sessionsAPI.getSessions(parseInt(id));
      const cropsToProcess: number[] = [];
      for (const s of sessions) {
        const resp = await sessionsAPI.getSessionFaceCrops(s.id);
        const missing = resp.face_crops.filter(c => !c.embedding_model).map(c => c.id);
        cropsToProcess.push(...missing);
      }

      if (cropsToProcess.length === 0) {
        setError('All face crops already have embeddings');
        return;
      }
      setEmbeddingProgress({ current: 0, total: cropsToProcess.length });

      // Sequentially generate embeddings per crop for progress visibility
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

      await loadClassData();
      setTimeout(() => {
        setEmbeddingProgress({ current: 0, total: 0 });
      }, 1500);
    } catch (err: any) {
      console.error('Error generating embeddings:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to generate embeddings';
      setError(errorMsg);
      setEmbeddingProgress({ current: 0, total: 0 });
    } finally {
      setGeneratingEmbeddings(false);
    }
  };

  const handleClusterCrops = async (options: ClusteringOptions) => {
    if (!id) return;

    try {
      setClusteringInProgress(true);
      setError('');
      setShowClusteringModal(false);

      const result = await classesAPI.clusterCrops(parseInt(id), options);
      
      setClusteringResult(result);
      setShowClusteringResultModal(true);

      // Reload class data and statistics
      await loadClassData();
    } catch (err: any) {
      console.error('Error clustering face crops:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to cluster face crops';
      setError(errorMsg);
    } finally {
      setClusteringInProgress(false);
    }
  };

  const handleAutoAssignAll = async (options: any) => {
    if (!id) return;

    try {
      setAutoAssigning(true);
      setError('');
      setShowAutoAssignModal(false);

      const result = await classesAPI.autoAssignAllCrops(parseInt(id), options);
      
      setAutoAssignResult(result);
      setShowAutoAssignResultModal(true);

      // Reload class data and statistics
      await loadClassData();
    } catch (err: any) {
      console.error('Error auto-assigning crops:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to auto-assign crops';
      setError(errorMsg);
    } finally {
      setAutoAssigning(false);
    }
  };

  const handleOpenManualAssign = () => {
    if (!id) return;
    // Navigate to the new manual assignment page
    navigate(`/classes/${id}/manual-assignment`);
  };

  // Management action handlers
  const handleClearClass = async () => {
    if (!id) return;
    
    try {
      setManagementProcessing(true);
      setError('');
      
      await classesAPI.clearClass(parseInt(id));
      
      setShowClearClassModal(false);
      
      // Reload class data
      await loadClassData();
    } catch (err: any) {
      console.error('Error clearing class:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to clear class';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  const handleResetSessions = async () => {
    if (!id) return;
    
    try {
      setManagementProcessing(true);
      setError('');
      
      await classesAPI.resetSessions(parseInt(id));
      
      setShowResetSessionsModal(false);
      
      // Reload class data
      await loadClassData();
    } catch (err: any) {
      console.error('Error resetting sessions:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to reset sessions';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  const handleClearStudents = async () => {
    if (!id) return;
    
    try {
      setManagementProcessing(true);
      setError('');
      
      await classesAPI.clearStudents(parseInt(id));
      
      setShowClearStudentsModal(false);
      
      // Reload class data
      await loadClassData();
    } catch (err: any) {
      console.error('Error clearing students:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to clear students';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  const handleResetStudents = async () => {
    if (!id) return;
    
    try {
      setManagementProcessing(true);
      setError('');
      
      await classesAPI.resetStudents(parseInt(id));
      
      setShowResetStudentsModal(false);
      
      // Reload class data
      await loadClassData();
    } catch (err: any) {
      console.error('Error resetting students:', err);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to reset students';
      setError(errorMsg);
    } finally {
      setManagementProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !classData) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-danger mb-4">Error</h2>
          <p className="text-gray-300 mb-4">{error || 'Class not found'}</p>
          <button
            onClick={() => navigate('/classes')}
            className="text-primary hover:text-primary-light transition-colors"
          >
            ← Back to Classes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg p-8">
      <div className="max-w-7xl mx-auto">
        {/* Processing Overlays */}
        <ProcessingOverlay 
          isProcessing={processingImages} 
          message="Processing images..." 
          progress={processProgress.total > 0 ? processProgress : undefined}
        />
        <ProcessingOverlay 
          isProcessing={generatingEmbeddings} 
          message="Generating embeddings..." 
          progress={embeddingProgress.total > 0 ? embeddingProgress : undefined}
        />

        {/* Back Button */}
        <button
          onClick={() => navigate('/classes')}
          className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Back to Classes</span>
        </button>

        {/* Breadcrumb */}
        <Breadcrumb
          items={[
            { label: 'Classes', href: '/classes' },
            { label: classData.name },
          ]}
          className="mb-6"
        />

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-100 mb-2">{classData.name}</h1>
          {classData.description && (
            <p className="text-gray-400">{classData.description}</p>
          )}
        </div>

        {/* Class-level Actions - New Hovering Menu */}
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
                      statistics
                        ? statistics.unprocessed_images_count > 0
                          ? `${statistics.unprocessed_images_count} unprocessed image${
                              statistics.unprocessed_images_count !== 1 ? 's' : ''
                            }`
                          : 'All images processed'
                        : 'Loading...'
                    }`,
                    icon: <Layers className="w-5 h-5" />,
                    onClick: handleProcessAllImages,
                    disabled: processingImages || (statistics?.unprocessed_images_count === 0),
                    isProcessing: processingImages,
                  },
                  {
                    id: 'generate-embeddings',
                    label: 'Generate Embeddings',
                    description: `Generate face embeddings for recognition. ${
                      statistics
                        ? `${statistics.crops_without_embeddings} of ${statistics.total_face_crops} face${
                            statistics.total_face_crops !== 1 ? 's' : ''
                          } need embedding${statistics.crops_without_embeddings !== 1 ? 's' : ''}`
                        : 'Loading...'
                    }`,
                    icon: <Sparkles className="w-5 h-5" />,
                    onClick: () => setShowEmbeddingModal(true),
                    disabled: generatingEmbeddings || (statistics?.crops_without_embeddings === 0),
                    isProcessing: generatingEmbeddings,
                  },
                  {
                    id: 'group-faces',
                    label: 'Group Student Faces',
                    description: 'Automatically cluster similar faces together to create student profiles',
                    icon: <Users className="w-5 h-5" />,
                    onClick: () => setShowClusteringModal(true),
                    disabled: !statistics || statistics.total_face_crops === 0 || clusteringInProgress,
                    isProcessing: clusteringInProgress,
                  },
                  {
                    id: 'identify-students',
                    label: 'Identify All Students',
                    description: 'Automatically identify and assign all unidentified faces to students',
                    icon: <Wand2 className="w-5 h-5" />,
                    onClick: () => setShowAutoAssignModal(true),
                    disabled: autoAssigning || !statistics || statistics.total_face_crops === 0,
                    isProcessing: autoAssigning,
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
                    icon: <UserCheck className="w-5 h-5" />,
                    onClick: handleOpenManualAssign,
                    disabled: !statistics || statistics.total_face_crops === 0,
                    isProcessing: false,
                  },
                ],
              },
              {
                label: 'Management',
                items: [
                  {
                    id: 'reset-sessions',
                    label: 'Reset All Sessions',
                    description: 'Remove all processing results while keeping original images',
                    icon: <RotateCcw className="w-5 h-5" />,
                    onClick: () => setShowResetSessionsModal(true),
                    disabled: managementProcessing || !statistics || statistics.session_count === 0,
                    isProcessing: false,
                  },
                  {
                    id: 'reset-students',
                    label: 'Reset Student Assignments',
                    description: 'Unassign all faces from students while keeping student records',
                    icon: <RotateCcw className="w-5 h-5" />,
                    onClick: () => setShowResetStudentsModal(true),
                    disabled: managementProcessing || !statistics || statistics.student_count === 0,
                    isProcessing: false,
                  },
                  {
                    id: 'clear-students',
                    label: 'Clear All Students',
                    description: 'Delete all student records and unassign all faces',
                    icon: <Trash2 className="w-5 h-5" />,
                    onClick: () => setShowClearStudentsModal(true),
                    disabled: managementProcessing || !statistics || statistics.student_count === 0,
                    isProcessing: false,
                  },
                  {
                    id: 'clear-class',
                    label: 'Clear All Class Data',
                    description: 'Delete all sessions, images, face crops, and students',
                    icon: <Trash2 className="w-5 h-5" />,
                    onClick: () => setShowClearClassModal(true),
                    disabled: managementProcessing,
                    isProcessing: false,
                  },
                ],
              },
            ]}
          />
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Students"
              value={statistics.student_count}
              icon="👥"
              iconColor="text-primary"
            />
            <StatCard
              label="Total Sessions"
              value={statistics.session_count}
              icon="📅"
              iconColor="text-success"
            />
            <StatCard
              label="Total Images"
              value={statistics.total_images}
              icon="📸"
              iconColor="text-purple-500"
            />
            <StatCard
              label="Identified Faces"
              value={`${statistics.identified_faces} / ${statistics.total_face_crops}`}
              icon="🔍"
              iconColor="text-warning"
            />
          </div>
        )}

        {/* Tabs */}
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} className="mb-6" />

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'sessions' && id && (
            <SessionsTab classId={parseInt(id)} onUpdate={loadClassData} />
          )}
          {activeTab === 'students' && id && (
            <StudentsTab classId={parseInt(id)} onUpdate={loadClassData} />
          )}
          {activeTab === 'report' && id && (
            <ReportTab classId={parseInt(id)} />
          )}
          {activeTab === 'notes' && id && (
            <NotesTab classId={parseInt(id)} onUpdate={loadClassData} />
          )}
        </div>
      </div>

      {/* Embedding Generation Modal */}
      <EmbeddingGenerationModal
        isOpen={showEmbeddingModal}
        onClose={() => setShowEmbeddingModal(false)}
        onGenerate={handleGenerateEmbeddings}
        isProcessing={generatingEmbeddings}
        unprocessedImagesCount={statistics?.total_images - statistics?.processed_images || 0}
        title="Generate Class Embeddings"
        description="Generate embeddings for all face crops across all sessions in this class to enable face recognition and matching."
      />

      {/* Clustering Modal */}
      <ClusteringModal
        isOpen={showClusteringModal}
        onClose={() => setShowClusteringModal(false)}
        onCluster={handleClusterCrops}
        isProcessing={clusteringInProgress}
        cropsWithoutEmbeddings={statistics?.crops_without_embeddings || 0}
        title="Cluster Class Faces"
        description="Cluster all face crops across all sessions in this class to automatically group similar faces and create student records."
      />

      {/* Clustering Result Modal */}
      {showClusteringResultModal && clusteringResult && (
        <Modal
          isOpen={showClusteringResultModal}
          onClose={() => {
            setShowClusteringResultModal(false);
            setClusteringResult(null);
          }}
          title="Clustering Results"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {clusteringResult.students_created}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Students Created
                </div>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {clusteringResult.crops_assigned}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Crops Assigned
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                  {clusteringResult.outliers}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Outliers
                </div>
              </div>
            </div>

            {/* Session Breakdown */}
            {clusteringResult.session_breakdown && clusteringResult.session_breakdown.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-2">Session Breakdown</h3>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                          Session
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                          Crops Assigned
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                          Unique Students
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {clusteringResult.session_breakdown.map((session: {
                        session_id: number;
                        session_name: string;
                        crops_assigned: number;
                        unique_students: number;
                      }) => (
                        <tr key={session.session_id}>
                          <td className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">
                            {session.session_name}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                            {session.crops_assigned}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                            {session.unique_students}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Created Students List */}
            {clusteringResult.created_students && clusteringResult.created_students.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-2">Created Students</h3>
                <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg max-h-40 overflow-y-auto">
                  <ul className="space-y-1">
                    {clusteringResult.created_students.map((name: string, index: number) => (
                      <li key={index} className="text-sm text-gray-700 dark:text-gray-300">
                        • {name}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => {
                  setShowClusteringResultModal(false);
                  setClusteringResult(null);
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowClusteringResultModal(false);
                  setClusteringResult(null);
                  setActiveTab('students');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                View Students
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Auto-Assign Modal */}
      <AutoAssignModal
        isOpen={showAutoAssignModal}
        onClose={() => setShowAutoAssignModal(false)}
        onAutoAssign={handleAutoAssignAll}
        isProcessing={autoAssigning}
        unidentifiedCropsCount={statistics?.total_face_crops ? (statistics.total_face_crops - statistics.identified_faces) : 0}
        title="Auto-Assign All Class Crops"
        description="Automatically assign all unidentified face crops across all sessions in this class to students based on similarity matching."
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

      {/* Management Confirmation Modals */}
      <ConfirmationModal
        isOpen={showClearClassModal}
        onClose={() => setShowClearClassModal(false)}
        onConfirm={handleClearClass}
        title="Clear All Class Data?"
        message="This will permanently delete all sessions, images, face crops, and students in this class. This action cannot be undone."
        confirmText="Clear All Data"
        isDestructive={true}
        isProcessing={managementProcessing}
      />

      <ConfirmationModal
        isOpen={showResetSessionsModal}
        onClose={() => setShowResetSessionsModal(false)}
        onConfirm={handleResetSessions}
        title="Reset All Sessions?"
        message="This will delete all face crops and reset processing status for all images in all sessions. Original images will be kept but you'll need to reprocess them. This action cannot be undone."
        confirmText="Reset Sessions"
        isDestructive={true}
        isProcessing={managementProcessing}
      />

      <ConfirmationModal
        isOpen={showClearStudentsModal}
        onClose={() => setShowClearStudentsModal(false)}
        onConfirm={handleClearStudents}
        title="Clear All Students?"
        message="This will permanently delete all student records and unassign all face crops. Manual attendance records will also be deleted. This action cannot be undone."
        confirmText="Clear Students"
        isDestructive={true}
        isProcessing={managementProcessing}
      />

      <ConfirmationModal
        isOpen={showResetStudentsModal}
        onClose={() => setShowResetStudentsModal(false)}
        onConfirm={handleResetStudents}
        title="Reset Student Assignments?"
        message="This will unassign all face crops from students and delete manual attendance records. Student records will be kept but will have no assignments. This action cannot be undone."
        confirmText="Reset Assignments"
        isDestructive={true}
        isProcessing={managementProcessing}
      />
    </div>
  );
};
