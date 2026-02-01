import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  imagesAPI, 
  faceCropsAPI, 
  sessionsAPI, 
  studentsAPI, 
  classesAPI 
} from '@/services/api';
import { Image, FaceCropDetail, Session, Student, Class } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ProcessingOverlay } from '@/components/ui/ProcessingSpinner';
import { 
  ArrowLeft, 
  Trash2, 
  UserPlus, 
  UserX, 
  Edit2, 
  Save,
  X as XIcon,
  Play,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const ImageDetailPage: React.FC = () => {
  const { classId, sessionId, imageId } = useParams<{
    classId: string;
    sessionId: string;
    imageId: string;
  }>();
  const navigate = useNavigate();

  // Data states
  const [image, setImage] = useState<Image | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [classData, setClassData] = useState<Class | null>(null);
  const [faceCrops, setFaceCrops] = useState<FaceCropDetail[]>([]);
  const [students, setStudents] = useState<Student[]>([]);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showDeleteCropModal, setShowDeleteCropModal] = useState(false);
  const [deletingCropId, setDeletingCropId] = useState<number | null>(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigningCropId, setAssigningCropId] = useState<number | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentSearchQuery, setStudentSearchQuery] = useState('');

  // Edit student modal states
  const [showEditStudentModal, setShowEditStudentModal] = useState(false);
  const [editingCropId, setEditingCropId] = useState<number | null>(null);
  const [editStudentData, setEditStudentData] = useState({
    first_name: '',
    last_name: '',
    student_id: '',
  });

  // Sorting state
  const [sortOption, setSortOption] = useState<'identified-first' | 'unidentified-first' | 'name-asc' | 'name-desc' | 'created-desc'>('identified-first');

  useEffect(() => {
    loadData();
  }, [classId, sessionId, imageId]);

  const loadData = async () => {
    if (!classId || !sessionId || !imageId) return;

    try {
      setLoading(true);
      setError(null);

      const [imageData, sessionData, classInfo, cropsData, studentsData] = await Promise.all([
        imagesAPI.getImage(parseInt(imageId)),
        sessionsAPI.getSession(parseInt(sessionId)),
        classesAPI.getClass(parseInt(classId)),
        faceCropsAPI.getFaceCrops(parseInt(imageId)),
        studentsAPI.getStudents(parseInt(classId)),
      ]);

      setImage(imageData);
      setSession(sessionData);
      setClassData(classInfo);
      setFaceCrops(cropsData);
      setStudents(studentsData);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load image data');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessImage = async () => {
    if (!imageId) return;

    try {
      setProcessing(true);
      setError(null);

      await imagesAPI.processImage(parseInt(imageId), {
        detector_backend: 'retinaface',
        confidence_threshold: 0.5,
        apply_background_effect: true,
      });

      // Reload data to get the processed image and face crops
      await loadData();
    } catch (err: any) {
      console.error('Error processing image:', err);
      setError(err.response?.data?.error || 'Failed to process image');
    } finally {
      setProcessing(false);
    }
  };

  const handleAssignStudent = async () => {
    if (!assigningCropId || !selectedStudentId) return;

    try {
      await faceCropsAPI.updateFaceCrop(assigningCropId, {
        student: selectedStudentId,
      });

      // Update local state
      setFaceCrops((prev) =>
        prev.map((crop) =>
          crop.id === assigningCropId
            ? {
                ...crop,
                student: selectedStudentId,
                student_name:
                  students.find((s) => s.id === selectedStudentId)?.full_name || null,
                is_identified: true,
              }
            : crop
        )
      );

      setShowAssignModal(false);
      setAssigningCropId(null);
      setSelectedStudentId(null);
    } catch (err) {
      console.error('Error assigning student:', err);
      setError('Failed to assign student');
    }
  };

  const handleCreateAndAssignNewStudent = async () => {
    if (!assigningCropId || !classId) return;

    try {
      const result = await faceCropsAPI.createAndAssignStudent(
        assigningCropId,
        parseInt(classId)
      );

      if (result.assigned && result.student) {
        // Update local state
        setFaceCrops((prev) =>
          prev.map((crop) =>
            crop.id === assigningCropId
              ? {
                  ...crop,
                  student: result.student.id,
                  student_name: result.student.full_name,
                  is_identified: true,
                }
              : crop
          )
        );

        // Add the new student to the students list
        setStudents((prev) => [...prev, result.student]);

        setShowAssignModal(false);
        setAssigningCropId(null);
        setSelectedStudentId(null);
      } else {
        setError('Failed to create and assign new student');
      }
    } catch (err: any) {
      console.error('Error creating and assigning student:', err);
      setError(err.response?.data?.error || 'Failed to create and assign new student');
    }
  };

  const handleUnassignStudent = async (cropId: number) => {
    try {
      await faceCropsAPI.unidentifyFaceCrop(cropId);

      // Update local state
      setFaceCrops((prev) =>
        prev.map((crop) =>
          crop.id === cropId
            ? { ...crop, student: null, student_name: null, is_identified: false }
            : crop
        )
      );
    } catch (err) {
      console.error('Error unassigning student:', err);
      setError('Failed to unassign student');
    }
  };

  const handleDeleteCrop = async () => {
    if (!deletingCropId) return;

    try {
      await faceCropsAPI.deleteFaceCrop(deletingCropId);

      // Update local state
      setFaceCrops((prev) => prev.filter((crop) => crop.id !== deletingCropId));

      // Update image face crop count
      if (image) {
        setImage({ ...image, face_crop_count: image.face_crop_count - 1 });
      }

      setShowDeleteCropModal(false);
      setDeletingCropId(null);
    } catch (err) {
      console.error('Error deleting crop:', err);
      setError('Failed to delete face crop');
      setShowDeleteCropModal(false);
      setDeletingCropId(null);
    }
  };

  const openEditStudentModal = (crop: FaceCropDetail) => {
    if (!crop.student) return;

    const student = students.find((s) => s.id === crop.student);
    if (!student) return;

    setEditingCropId(crop.id);
    setEditStudentData({
      first_name: student.first_name,
      last_name: student.last_name,
      student_id: student.student_id,
    });
    setShowEditStudentModal(true);
  };

  const handleEditStudent = async () => {
    if (!editingCropId) return;

    const crop = faceCrops.find((c) => c.id === editingCropId);
    if (!crop || !crop.student) return;

    try {
      const updatedStudent = await studentsAPI.updateStudent(crop.student, editStudentData);

      // Update local state
      setStudents((prev) =>
        prev.map((s) => (s.id === updatedStudent.id ? updatedStudent : s))
      );
      setFaceCrops((prev) =>
        prev.map((c) =>
          c.id === editingCropId ? { ...c, student_name: updatedStudent.full_name } : c
        )
      );

      setShowEditStudentModal(false);
      setEditingCropId(null);
    } catch (err) {
      console.error('Error updating student:', err);
      setError('Failed to update student information');
    }
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

  const sortFaceCrops = (crops: FaceCropDetail[]) => {
    const sorted = [...crops];
    
    switch (sortOption) {
      case 'identified-first':
        return sorted.sort((a, b) => {
          if (a.is_identified === b.is_identified) return 0;
          return a.is_identified ? -1 : 1;
        });
      case 'unidentified-first':
        return sorted.sort((a, b) => {
          if (a.is_identified === b.is_identified) return 0;
          return a.is_identified ? 1 : -1;
        });
      case 'name-asc':
        return sorted.sort((a, b) => {
          const nameA = a.student_name || 'zzz'; // Push unnamed to end
          const nameB = b.student_name || 'zzz';
          return nameA.localeCompare(nameB);
        });
      case 'name-desc':
        return sorted.sort((a, b) => {
          const nameA = a.student_name || 'zzz'; // Push unnamed to end
          const nameB = b.student_name || 'zzz';
          return nameB.localeCompare(nameA);
        });
      case 'created-desc':
        return sorted.sort((a, b) => {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
      default:
        return sorted;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!image || !session || !classData) {
    return (
      <div className="p-8">
        <p className="text-danger">Image not found</p>
      </div>
    );
  }

  const breadcrumbItems = [
    { label: 'Classes', path: '/classes' },
    { label: classData.name, path: `/classes/${classId}` },
    { label: session.name, path: `/classes/${classId}/sessions/${sessionId}` },
    { label: 'Image Details' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Processing Overlay */}
      <ProcessingOverlay isProcessing={processing} message="Processing image..." />

      {/* Back Button */}
      <button
        onClick={() => navigate(`/classes/${classId}/sessions/${sessionId}`)}
        className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-medium">Back to Session</span>
      </button>

      <Breadcrumb items={breadcrumbItems} />

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

      {/* Image Header */}
      <Card className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Image Details</h1>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>
                Uploaded: {new Date(image.upload_date).toLocaleString()}
              </span>
              <span>Face Crops: {faceCrops.length}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={image.is_processed ? 'success' : 'warning'}>
              {image.is_processed ? 'Processed' : 'Pending'}
            </Badge>
            {!image.is_processed && (
              <Button onClick={handleProcessImage} disabled={processing}>
                <Play className="w-4 h-4 mr-2" />
                Process Image
              </Button>
            )}
          </div>
        </div>

        {/* Image Display */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Original Image */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-white">Original Image</h3>
            <div className="aspect-video bg-dark-bg rounded-lg overflow-hidden border border-dark-border">
              <img
                src={getImageUrl(image.original_image_path)}
                alt="Original"
                className="w-full h-full object-contain"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23334155" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23cbd5e1" font-family="sans-serif" font-size="14"%3ENo Preview%3C/text%3E%3C/svg%3E';
                }}
              />
            </div>
          </div>

          {/* Processed Image */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-white">Processed Image</h3>
            <div className="aspect-video bg-dark-bg rounded-lg overflow-hidden border border-dark-border">
              {image.processed_image_path ? (
                <img
                  src={getImageUrl(image.processed_image_path)}
                  alt="Processed"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23334155" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23cbd5e1" font-family="sans-serif" font-size="14"%3ENo Preview%3C/text%3E%3C/svg%3E';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Not processed yet</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Face Crops Section */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Face Crops</h2>
            <p className="text-sm text-gray-400 mt-1">
              {faceCrops.length} face{faceCrops.length !== 1 ? 's' : ''} detected
            </p>
          </div>
          
          {faceCrops.length > 0 && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Sort by:</label>
              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value as any)}
                className="bg-dark-bg border border-dark-border rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary"
              >
                <option value="identified-first">Identified First</option>
                <option value="unidentified-first">Unidentified First</option>
                <option value="name-asc">Name (A-Z)</option>
                <option value="name-desc">Name (Z-A)</option>
                <option value="created-desc">Newest First</option>
              </select>
            </div>
          )}
        </div>

        {faceCrops.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-dark-border rounded-lg">
            <AlertCircle className="w-12 h-12 text-gray-500 mx-auto mb-3" />
            <p className="text-gray-400 mb-2">No face crops yet</p>
            <p className="text-sm text-gray-500">
              {image.is_processed
                ? 'No faces detected in this image'
                : 'Process the image to detect faces'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {sortFaceCrops(faceCrops).map((crop) => (
              <div
                key={crop.id}
                className="relative group bg-dark-card rounded-lg overflow-hidden border border-dark-border hover:border-primary transition-colors cursor-pointer"
                onClick={() => navigate(`/classes/${classId}/sessions/${sessionId}/images/${imageId}/crops/${crop.id}`)}
              >
                {/* Face Crop Image */}
                <div className="aspect-square bg-dark-bg flex items-center justify-center">
                  <img
                    src={getImageUrl(crop.crop_image_path)}
                    alt={`Face ${crop.id}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23334155" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23cbd5e1" font-family="sans-serif" font-size="14"%3ENo Preview%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </div>

                {/* Student Info */}
                <div className="p-3 bg-dark-bg">
                  {crop.is_identified && crop.student_name ? (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="success" className="text-xs">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Identified
                        </Badge>
                      </div>
                      <p className="text-sm text-white font-medium truncate">
                        {crop.student_name}
                      </p>
                    </div>
                  ) : (
                    <div>
                      <Badge variant="warning" className="text-xs mb-2">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Unidentified
                      </Badge>
                      <p className="text-xs text-gray-500">No student assigned</p>
                    </div>
                  )}
                </div>

                {/* Action Buttons Overlay */}
                <div className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-4">
                  {crop.is_identified && crop.student ? (
                    <>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          openEditStudentModal(crop);
                        }}
                        className="w-full"
                      >
                        <Edit2 className="w-3 h-3 mr-1" />
                        Edit Info
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUnassignStudent(crop.id);
                        }}
                        className="w-full"
                      >
                        <UserX className="w-3 h-3 mr-1" />
                        Unassign
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setAssigningCropId(crop.id);
                        setShowAssignModal(true);
                      }}
                      className="w-full"
                    >
                      <UserPlus className="w-3 h-3 mr-1" />
                      Assign Student
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeletingCropId(crop.id);
                      setShowDeleteCropModal(true);
                    }}
                    className="w-full"
                  >
                    <Trash2 className="w-3 h-3 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Assign Student Modal */}
      <Modal
        isOpen={showAssignModal}
        onClose={() => {
          setShowAssignModal(false);
          setAssigningCropId(null);
          setSelectedStudentId(null);
          setStudentSearchQuery('');
        }}
        title="Assign Student to Face Crop"
      >
        <div className="space-y-4">
          <p className="text-gray-300">Select a student to assign to this face crop:</p>

          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search by name or student ID..."
              value={studentSearchQuery}
              onChange={(e) => setStudentSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
            />
            {studentSearchQuery && (
              <button
                onClick={() => setStudentSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                <XIcon className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto space-y-2">
            {students
              .filter((student) => {
                if (!studentSearchQuery) return true;
                const query = studentSearchQuery.toLowerCase();
                return (
                  student.first_name.toLowerCase().includes(query) ||
                  student.last_name.toLowerCase().includes(query) ||
                  student.full_name.toLowerCase().includes(query) ||
                  student.student_id.toLowerCase().includes(query) ||
                  student.email?.toLowerCase().includes(query)
                );
              })
              .map((student) => (
                <button
                  key={student.id}
                  onClick={() => setSelectedStudentId(student.id)}
                  className={`w-full p-3 rounded-lg border transition-colors text-left ${
                    selectedStudentId === student.id
                      ? 'border-primary bg-primary/10'
                      : 'border-dark-border hover:border-gray-600 bg-dark-hover'
                  }`}
                >
                  <p className="text-white font-medium">{student.full_name}</p>
                  {student.student_id && (
                    <p className="text-xs text-gray-400 mt-1">ID: {student.student_id}</p>
                  )}
                  {student.email && (
                    <p className="text-xs text-gray-400">{student.email}</p>
                  )}
                </button>
              ))}
          </div>

          {students.filter((student) => {
            if (!studentSearchQuery) return true;
            const query = studentSearchQuery.toLowerCase();
            return (
              student.first_name.toLowerCase().includes(query) ||
              student.last_name.toLowerCase().includes(query) ||
              student.full_name.toLowerCase().includes(query) ||
              student.student_id.toLowerCase().includes(query) ||
              student.email?.toLowerCase().includes(query)
            );
          }).length === 0 && (
            <p className="text-gray-500 text-center py-4">
              {studentSearchQuery ? 'No students found matching your search.' : 'No students available. Add students to the class first.'}
            </p>
          )}

          <div className="flex gap-3 pt-4 border-t border-dark-border">
            {classId && (
              <Button
                onClick={handleCreateAndAssignNewStudent}
                disabled={!assigningCropId}
                variant="secondary"
                className="flex-1"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Create New
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() => {
                setShowAssignModal(false);
                setAssigningCropId(null);
                setSelectedStudentId(null);
                setStudentSearchQuery('');
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAssignStudent}
              disabled={!selectedStudentId}
              className="flex-1"
            >
              <Save className="w-4 h-4 mr-2" />
              Assign
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Student Modal */}
      <Modal
        isOpen={showEditStudentModal}
        onClose={() => {
          setShowEditStudentModal(false);
          setEditingCropId(null);
        }}
        title="Edit Student Information"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              First Name
            </label>
            <input
              type="text"
              value={editStudentData.first_name}
              onChange={(e) =>
                setEditStudentData({ ...editStudentData, first_name: e.target.value })
              }
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Last Name
            </label>
            <input
              type="text"
              value={editStudentData.last_name}
              onChange={(e) =>
                setEditStudentData({ ...editStudentData, last_name: e.target.value })
              }
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Student ID
            </label>
            <input
              type="text"
              value={editStudentData.student_id}
              onChange={(e) =>
                setEditStudentData({ ...editStudentData, student_id: e.target.value })
              }
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowEditStudentModal(false);
                setEditingCropId(null);
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleEditStudent}
              disabled={!editStudentData.first_name || !editStudentData.last_name}
              className="flex-1"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Crop Modal */}
      <Modal
        isOpen={showDeleteCropModal}
        onClose={() => {
          setShowDeleteCropModal(false);
          setDeletingCropId(null);
        }}
        title="Delete Face Crop"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete this face crop?
          </p>

          <div className="p-3 bg-warning bg-opacity-10 border border-warning rounded-lg">
            <p className="text-warning text-sm">
              This action cannot be undone. The face crop will be permanently deleted.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowDeleteCropModal(false);
                setDeletingCropId(null);
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteCrop} className="flex-1">
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ImageDetailPage;
