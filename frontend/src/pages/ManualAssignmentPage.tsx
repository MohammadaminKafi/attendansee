import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { classesAPI, faceCropsAPI, studentsAPI } from '@/services/api';
import { Class, EnhancedCropSuggestion, SimilarFaceEnhanced, Student } from '@/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Modal } from '@/components/ui/Modal';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  UserCheck,
  UserPlus,
  AlertCircle,
  CheckCircle,
  X as XIcon,
  Filter,
  Layers,
  Image as ImageIcon,
  Calendar,
  Users,
  Search,
} from 'lucide-react';

type CropFilter = 'all' | 'identified' | 'unidentified';
type ScopeFilter = 'class' | 'session' | 'image';

const TOP_K_OPTIONS = [5, 10, 15, 20];

export const ManualAssignmentPage: React.FC = () => {
  const { classId } = useParams<{ classId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Get initial parameters from URL - these determine WHICH crops to work on (fixed)
  const initialSessionId = searchParams.get('session_id');
  const initialImageId = searchParams.get('image_id');
  // Determine the source scope (which crops to show) - this is fixed based on navigation
  const sourceScope: ScopeFilter = initialImageId ? 'image' : (initialSessionId ? 'session' : 'class');

  // Data states
  const [classData, setClassData] = useState<Class | null>(null);
  const [suggestions, setSuggestions] = useState<EnhancedCropSuggestion[]>([]);
  const [students, setStudents] = useState<Student[]>([]);

  // Filter states
  const [cropFilter, setCropFilter] = useState<CropFilter>('unidentified');
  const [searchScope, setSearchScope] = useState<ScopeFilter>('class');  // Where to search for similar faces
  const [kIdentified, setKIdentified] = useState(5);
  const [kUnidentified, setKUnidentified] = useState(5);
  const [customKIdentified, setCustomKIdentified] = useState('');
  const [customKUnidentified, setCustomKUnidentified] = useState('');
  const [pendingKIdentified, setPendingKIdentified] = useState('');  // For Enter key submission
  const [pendingKUnidentified, setPendingKUnidentified] = useState('');  // For Enter key submission

  // Navigation states
  const [currentIndex, setCurrentIndex] = useState(0);
  const [assignedCrops, setAssignedCrops] = useState<Set<number>>(new Set());

  // Loading/UI states
  const [loading, setLoading] = useState(true);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Create Student Modal states
  const [showCreateStudentModal, setShowCreateStudentModal] = useState(false);
  const [createStudentFor, setCreateStudentFor] = useState<'current' | 'match' | null>(null);
  const [matchCropId, setMatchCropId] = useState<number | null>(null);
  const [newStudentData, setNewStudentData] = useState({
    first_name: '',
    last_name: '',
    student_id: '',
    email: '',
  });

  // Select Existing Student Modal states
  const [showSelectStudentModal, setShowSelectStudentModal] = useState(false);
  const [studentSearchQuery, setStudentSearchQuery] = useState('');

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

  // Load initial data
  useEffect(() => {
    if (!classId) return;

    const loadInitialData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [classInfo, studentsData] = await Promise.all([
          classesAPI.getClass(parseInt(classId)),
          studentsAPI.getStudents(parseInt(classId)),
        ]);

        setClassData(classInfo);
        setStudents(studentsData);
      } catch (err: any) {
        console.error('Error loading initial data:', err);
        setError(err.response?.data?.error || 'Failed to load class data');
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [classId]);

  // Load suggestions when filters change
  const loadSuggestions = useCallback(async () => {
    if (!classId) return;

    try {
      setLoadingSuggestions(true);
      setError(null);

      const params: {
        filter: CropFilter;
        k_identified: number;
        k_unidentified: number;
        scope: ScopeFilter;
        search_scope: ScopeFilter;
        session_id?: number;
        image_id?: number;
        limit: number;
      } = {
        filter: cropFilter,
        k_identified: kIdentified,
        k_unidentified: kUnidentified,
        scope: sourceScope,  // Fixed based on navigation - which crops to show
        search_scope: searchScope,  // User-selectable - where to search for similar faces
        limit: 100,
      };

      // Add session/image ID if available (for filtering crops to display)
      if (initialSessionId) {
        params.session_id = parseInt(initialSessionId);
      }
      if (initialImageId) {
        params.image_id = parseInt(initialImageId);
      }

      const result = await classesAPI.getSuggestAssignmentsEnhanced(parseInt(classId), params);
      setSuggestions(result.suggestions);

      // Reset to first unassigned crop
      if (result.suggestions.length > 0) {
        const firstUnassigned = result.suggestions.findIndex(
          (s) => !assignedCrops.has(s.crop_id)
        );
        setCurrentIndex(firstUnassigned !== -1 ? firstUnassigned : 0);
      }
    } catch (err: any) {
      console.error('Error loading suggestions:', err);
      setError(err.response?.data?.error || 'Failed to load suggestions');
    } finally {
      setLoadingSuggestions(false);
    }
  }, [classId, cropFilter, searchScope, kIdentified, kUnidentified, sourceScope, initialSessionId, initialImageId, assignedCrops]);

  // Load suggestions on mount and when dependencies change
  useEffect(() => {
    if (classData) {
      loadSuggestions();
    }
  }, [classData, cropFilter, searchScope, kIdentified, kUnidentified]);

  // Current crop
  const currentCrop = suggestions[currentIndex];
  const totalCrops = suggestions.length;
  const progressPercent = totalCrops > 0 ? (assignedCrops.size / totalCrops) * 100 : 0;

  // Navigation handlers
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
      // Find first unassigned
      const firstUnassigned = suggestions.findIndex((s: EnhancedCropSuggestion) => !assignedCrops.has(s.crop_id));
      if (firstUnassigned !== -1 && firstUnassigned !== currentIndex) {
        setCurrentIndex(firstUnassigned);
      }
    }
  };

  // Move to next unassigned crop
  const moveToNextUnassigned = () => {
    setTimeout(() => {
      const nextUnassigned = suggestions.findIndex(
        (s: EnhancedCropSuggestion, idx: number) => idx > currentIndex && !assignedCrops.has(s.crop_id)
      );
      if (nextUnassigned !== -1) {
        setCurrentIndex(nextUnassigned);
      } else {
        // Check before current
        const prevUnassigned = suggestions.findIndex((s: EnhancedCropSuggestion) => !assignedCrops.has(s.crop_id));
        if (prevUnassigned !== -1) {
          setCurrentIndex(prevUnassigned);
        }
      }
      setSuccessMessage(null);
    }, 800);
  };

  // Assign from identified face
  const handleAssignFromIdentified = async (face: SimilarFaceEnhanced) => {
    if (!currentCrop || !face.student_id) return;

    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);

      const result = await faceCropsAPI.assignFromCandidate(
        currentCrop.crop_id,
        face.crop_id,
        face.similarity
      );

      if (result.assigned && result.student_name) {
        setSuccessMessage(`Assigned to ${result.student_name}`);
        setAssignedCrops((prev: Set<number>) => new Set(prev).add(currentCrop.crop_id));
        moveToNextUnassigned();
      } else {
        setError(result.message || 'Failed to assign');
      }
    } catch (err: any) {
      console.error('Error assigning crop:', err);
      setError(err.response?.data?.error || 'Failed to assign crop');
    } finally {
      setProcessing(false);
    }
  };

  // Open create student modal for matching with unidentified face
  const handleMatchWithUnidentified = (face: SimilarFaceEnhanced) => {
    setCreateStudentFor('match');
    setMatchCropId(face.crop_id);
    setNewStudentData({
      first_name: '',
      last_name: '',
      student_id: '',
      email: '',
    });
    generateDefaultStudentName();
    setShowCreateStudentModal(true);
  };

  // Open create student modal for current crop
  const handleCreateNewStudent = () => {
    setCreateStudentFor('current');
    setMatchCropId(null);
    setNewStudentData({
      first_name: '',
      last_name: '',
      student_id: '',
      email: '',
    });
    generateDefaultStudentName();
    setShowCreateStudentModal(true);
  };

  // Generate default student name
  const generateDefaultStudentName = () => {
    const existingNumbers = students
      .filter((s: Student) => s.first_name === 'Student' && s.last_name.startsWith('#'))
      .map((s: Student) => parseInt(s.last_name.slice(1)))
      .filter((n: number) => !isNaN(n));

    let nextNumber = 1;
    while (existingNumbers.includes(nextNumber)) {
      nextNumber++;
    }

    setNewStudentData((prev: typeof newStudentData) => ({
      ...prev,
      first_name: 'Student',
      last_name: `#${nextNumber}`,
    }));
  };

  // Create student and assign
  const handleCreateStudentSubmit = async () => {
    if (!currentCrop || !classId) return;

    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);

      const cropToAssign = createStudentFor === 'match' && matchCropId ? matchCropId : currentCrop.crop_id;

      const result = await faceCropsAPI.createAndAssignStudent(cropToAssign, parseInt(classId), {
        first_name: newStudentData.first_name || undefined,
        last_name: newStudentData.last_name || undefined,
        student_id: newStudentData.student_id || undefined,
        email: newStudentData.email || undefined,
      });

      if (result.assigned && result.student_name) {
        // Add new student to list
        if (result.student) {
          setStudents((prev: Student[]) => [...prev, result.student]);
        }

        // If we created for current crop, also assign to the matching unidentified if selected
        if (createStudentFor === 'match' && matchCropId) {
          // Now assign the current crop to the newly created student
          await faceCropsAPI.assignFromCandidate(currentCrop.crop_id, matchCropId, 1.0);
          setSuccessMessage(`Created ${result.student_name} and assigned both crops`);
        } else {
          setSuccessMessage(`Created and assigned to ${result.student_name}`);
        }

        setAssignedCrops((prev: Set<number>) => new Set(prev).add(currentCrop.crop_id));
        setShowCreateStudentModal(false);
        moveToNextUnassigned();
      } else {
        setError('Failed to create and assign student');
      }
    } catch (err: any) {
      console.error('Error creating student:', err);
      setError(err.response?.data?.error || 'Failed to create and assign student');
    } finally {
      setProcessing(false);
    }
  };

  // Assign to existing student
  const handleAssignToStudent = async (student: Student) => {
    if (!currentCrop) return;

    try {
      setProcessing(true);
      setError(null);
      setSuccessMessage(null);

      // Use the assignToStudent endpoint
      const result = await faceCropsAPI.assignToStudent(currentCrop.crop_id, student.id, 1.0);

      if (result.success) {
        setSuccessMessage(`Assigned to ${student.full_name}`);
        setAssignedCrops((prev: Set<number>) => new Set(prev).add(currentCrop.crop_id));
        setShowSelectStudentModal(false);
        moveToNextUnassigned();
      } else {
        setError(result.message || 'Failed to assign');
      }
    } catch (err: any) {
      console.error('Error assigning to student:', err);
      setError(err.response?.data?.error || 'Failed to assign to student');
    } finally {
      setProcessing(false);
    }
  };

  // Handle K value change - button click
  const handleKIdentifiedChange = (value: number) => {
    setKIdentified(value);
    setCustomKIdentified('');
    setPendingKIdentified('');
  };

  const handleKUnidentifiedChange = (value: number) => {
    setKUnidentified(value);
    setCustomKUnidentified('');
    setPendingKUnidentified('');
  };

  // Handle custom K on Enter key
  const handleCustomKIdentifiedKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const num = parseInt(pendingKIdentified);
      if (!isNaN(num) && num > 0 && num <= 50) {
        setKIdentified(num);
        setCustomKIdentified(pendingKIdentified);
      }
    }
  };

  const handleCustomKUnidentifiedKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const num = parseInt(pendingKUnidentified);
      if (!isNaN(num) && num > 0 && num <= 50) {
        setKUnidentified(num);
        setCustomKUnidentified(pendingKUnidentified);
      }
    }
  };

  // Filter students for search
  const filteredStudents = students.filter((student: Student) =>
    student.full_name.toLowerCase().includes(studentSearchQuery.toLowerCase()) ||
    (student.student_id && student.student_id.toLowerCase().includes(studentSearchQuery.toLowerCase()))
  );

  // Build breadcrumb
  const buildBreadcrumbItems = () => {
    const items: { label: string; href?: string }[] = [{ label: 'Classes', href: '/classes' }];
    if (classData) {
      items.push({ label: classData.name, href: `/classes/${classId}` });
    }
    items.push({ label: 'Manual Assignment' });
    return items;
  };

  // Handle back navigation
  const handleBack = () => {
    if (initialImageId && initialSessionId) {
      navigate(`/classes/${classId}/sessions/${initialSessionId}/images/${initialImageId}`);
    } else if (initialSessionId) {
      navigate(`/classes/${classId}/sessions/${initialSessionId}`);
    } else {
      navigate(`/classes/${classId}`);
    }
  };

  // Check if current crop is assigned
  const isCurrentCropAssigned = currentCrop ? assignedCrops.has(currentCrop.crop_id) : false;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!classData) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-danger mb-4">Error</h2>
          <p className="text-gray-300 mb-4">{error || 'Class not found'}</p>
          <Button onClick={() => navigate('/classes')}>← Back to Classes</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg p-8">
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">
            Back to {initialImageId ? 'Image' : initialSessionId ? 'Session' : 'Class'}
          </span>
        </button>

        {/* Breadcrumb */}
        <Breadcrumb items={buildBreadcrumbItems()} className="mb-6" />

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-100 mb-2">Manual Face Assignment</h1>
          <p className="text-gray-400">
            Review and assign faces to students for {classData.name}
            {sourceScope !== 'class' && (
              <span className="ml-2 text-xs bg-dark-border px-2 py-1 rounded">
                {sourceScope === 'session' ? 'Session' : 'Image'} scope
              </span>
            )}
          </p>
        </div>

        {/* Filters Row */}
        <Card className="p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* Crop Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">Show:</span>
              <div className="flex gap-1">
                {(['unidentified', 'identified', 'all'] as CropFilter[]).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setCropFilter(filter)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      cropFilter === filter
                        ? 'bg-primary text-white'
                        : 'bg-dark-bg text-gray-400 hover:bg-dark-hover hover:text-white'
                    }`}
                  >
                    {filter.charAt(0).toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Search Scope Filter - controls WHERE to search for similar faces */}
            <div className="flex items-center gap-2 border-l border-dark-border pl-4">
              <Search className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">Search similar in:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => setSearchScope('class')}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1 ${
                    searchScope === 'class'
                      ? 'bg-primary text-white'
                      : 'bg-dark-bg text-gray-400 hover:bg-dark-hover hover:text-white'
                  }`}
                >
                  <Layers className="w-3 h-3" />
                  Class
                </button>
                <button
                  onClick={() => setSearchScope('session')}
                  disabled={!initialSessionId}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1 ${
                    searchScope === 'session'
                      ? 'bg-primary text-white'
                      : 'bg-dark-bg text-gray-400 hover:bg-dark-hover hover:text-white'
                  } ${!initialSessionId ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <Calendar className="w-3 h-3" />
                  Session
                </button>
                <button
                  onClick={() => setSearchScope('image')}
                  disabled={!initialImageId}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1 ${
                    searchScope === 'image'
                      ? 'bg-primary text-white'
                      : 'bg-dark-bg text-gray-400 hover:bg-dark-hover hover:text-white'
                  } ${!initialImageId ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <ImageIcon className="w-3 h-3" />
                  Image
                </button>
              </div>
            </div>

            {/* Refresh Button */}
            <Button
              variant="secondary"
              size="sm"
              onClick={loadSuggestions}
              disabled={loadingSuggestions}
              className="ml-auto"
            >
              {loadingSuggestions ? 'Loading...' : 'Refresh'}
            </Button>
          </div>
        </Card>

        {/* Progress Bar */}
        <Card className="p-4 mb-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">
                Progress: {assignedCrops.size} / {totalCrops} assigned
              </span>
              <span className="text-primary font-medium">{progressPercent.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-dark-border rounded-full h-2 overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </Card>

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

        {/* Main Content */}
        {loadingSuggestions ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : suggestions.length === 0 ? (
          <Card className="p-8 text-center">
            <AlertCircle className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">No Faces Found</h3>
            <p className="text-gray-400 mb-4">
              No face crops match the current filter criteria.
              {cropFilter === 'unidentified' && ' Try changing the filter to see all faces.'}
            </p>
            <Button onClick={handleBack}>Go Back</Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Current Crop Panel */}
            <Card className="lg:col-span-1 overflow-hidden">
              <div className="bg-dark-hover p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">
                    Current Face
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
                    <span className="text-sm text-gray-400 min-w-[60px] text-center">
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

              <div className="p-4">
                {currentCrop && (
                  <>
                    <div className="aspect-square bg-dark-bg rounded-lg overflow-hidden border-2 border-primary/30 mb-4">
                      <img
                        src={getImageUrl(currentCrop.crop_image_path)}
                        alt={`Crop ${currentCrop.crop_id}`}
                        className="w-full h-full object-contain"
                      />
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Session:</span>
                        <span className="text-white">{currentCrop.session_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Status:</span>
                        <span
                          className={
                            currentCrop.is_identified ? 'text-success' : 'text-warning'
                          }
                        >
                          {currentCrop.is_identified
                            ? `Identified: ${currentCrop.student_name}`
                            : 'Unidentified'}
                        </span>
                      </div>
                    </div>

                    <div className="mt-4 space-y-2">
                      <Button
                        variant="secondary"
                        onClick={handleSkip}
                        disabled={processing}
                        className="w-full"
                      >
                        Skip This Face
                      </Button>
                      {!currentCrop.is_identified && (
                        <>
                          <Button
                            variant="secondary"
                            onClick={() => {
                              setStudentSearchQuery('');
                              setShowSelectStudentModal(true);
                            }}
                            disabled={processing || isCurrentCropAssigned || students.length === 0}
                            className="w-full"
                          >
                            <Users className="w-4 h-4 mr-2" />
                            Assign to Existing Student
                          </Button>
                          <Button
                            onClick={handleCreateNewStudent}
                            disabled={processing || isCurrentCropAssigned}
                            className="w-full"
                          >
                            <UserPlus className="w-4 h-4 mr-2" />
                            Create New Student
                          </Button>
                        </>
                      )}
                    </div>
                  </>
                )}
              </div>
            </Card>

            {/* Similar Faces Panel */}
            <Card className="lg:col-span-2 overflow-hidden">
              <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-dark-border">
                {/* Identified Similar Faces */}
                <div className="flex flex-col">
                  <div className="bg-dark-hover p-4 border-b border-dark-border">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-base font-semibold text-white flex items-center gap-2">
                        <UserCheck className="w-4 h-4 text-success" />
                        Identified Faces
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-gray-400">Top-K:</span>
                      {TOP_K_OPTIONS.map((k) => (
                        <button
                          key={k}
                          onClick={() => handleKIdentifiedChange(k)}
                          className={`px-2 py-0.5 text-xs rounded transition-colors ${
                            kIdentified === k && !customKIdentified
                              ? 'bg-primary text-white'
                              : 'bg-dark-bg text-gray-400 hover:bg-dark-card hover:text-white'
                          }`}
                        >
                          {k}
                        </button>
                      ))}
                      <input
                        type="number"
                        placeholder="Custom (Enter)"
                        value={pendingKIdentified}
                        onChange={(e) => setPendingKIdentified(e.target.value)}
                        onKeyDown={handleCustomKIdentifiedKeyDown}
                        className="w-24 px-2 py-0.5 text-xs bg-dark-bg border border-dark-border rounded text-white placeholder-gray-500"
                        min={1}
                        max={50}
                      />
                    </div>
                  </div>

                  <div className="p-3 flex-1 overflow-y-auto max-h-[60vh]">
                    {!currentCrop?.similar_identified?.length ? (
                      <div className="text-center py-8">
                        <AlertCircle className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                        <p className="text-sm text-gray-400">No identified similar faces</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-2">
                        {currentCrop.similar_identified.map((face) => (
                          <div
                            key={face.crop_id}
                            className="rounded-lg border border-primary/30 bg-dark-hover overflow-hidden"
                          >
                            <div className="aspect-square bg-dark-bg">
                              <img
                                src={getImageUrl(face.crop_image_path)}
                                alt={`Similar ${face.crop_id}`}
                                className="w-full h-full object-contain"
                              />
                            </div>
                            <div className="p-1.5 space-y-1">
                              <p className="text-xs font-medium text-white truncate">
                                {face.student_name}
                              </p>
                              <div className="flex justify-between text-xs">
                                <span className="text-gray-400">Sim:</span>
                                <span className="text-primary font-medium">
                                  {(face.similarity * 100).toFixed(0)}%
                                </span>
                              </div>
                              <Button
                                size="sm"
                                onClick={() => handleAssignFromIdentified(face)}
                                disabled={processing || isCurrentCropAssigned}
                                className="w-full text-xs py-1"
                              >
                                <UserCheck className="w-3 h-3 mr-1" />
                                Assign
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Unidentified Similar Faces */}
                <div className="flex flex-col">
                  <div className="bg-dark-hover p-4 border-b border-dark-border">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-base font-semibold text-white flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-warning" />
                        Unidentified Faces
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-gray-400">Top-K:</span>
                      {TOP_K_OPTIONS.map((k) => (
                        <button
                          key={k}
                          onClick={() => handleKUnidentifiedChange(k)}
                          className={`px-2 py-0.5 text-xs rounded transition-colors ${
                            kUnidentified === k && !customKUnidentified
                              ? 'bg-primary text-white'
                              : 'bg-dark-bg text-gray-400 hover:bg-dark-card hover:text-white'
                          }`}
                        >
                          {k}
                        </button>
                      ))}
                      <input
                        type="number"
                        placeholder="Custom (Enter)"
                        value={pendingKUnidentified}
                        onChange={(e) => setPendingKUnidentified(e.target.value)}
                        onKeyDown={handleCustomKUnidentifiedKeyDown}
                        className="w-24 px-2 py-0.5 text-xs bg-dark-bg border border-dark-border rounded text-white placeholder-gray-500"
                        min={1}
                        max={50}
                      />
                    </div>
                  </div>

                  <div className="p-3 flex-1 overflow-y-auto max-h-[60vh]">
                    {!currentCrop?.similar_unidentified?.length ? (
                      <div className="text-center py-8">
                        <AlertCircle className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                        <p className="text-sm text-gray-400">No unidentified similar faces</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-2">
                        {currentCrop.similar_unidentified.map((face) => (
                          <div
                            key={face.crop_id}
                            className="rounded-lg border border-dark-border bg-dark-card overflow-hidden"
                          >
                            <div className="aspect-square bg-dark-bg">
                              <img
                                src={getImageUrl(face.crop_image_path)}
                                alt={`Similar ${face.crop_id}`}
                                className="w-full h-full object-contain"
                              />
                            </div>
                            <div className="p-1.5 space-y-1">
                              <p className="text-xs text-gray-500 italic">Unidentified</p>
                              <div className="flex justify-between text-xs">
                                <span className="text-gray-400">Sim:</span>
                                <span className="text-primary font-medium">
                                  {(face.similarity * 100).toFixed(0)}%
                                </span>
                              </div>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleMatchWithUnidentified(face)}
                                disabled={processing || isCurrentCropAssigned}
                                className="w-full text-xs py-1"
                              >
                                <UserPlus className="w-3 h-3 mr-1" />
                                Match
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Create Student Modal */}
        <Modal
          isOpen={showCreateStudentModal}
          onClose={() => setShowCreateStudentModal(false)}
          title="Create New Student"
          className="max-w-md"
        >
          <div className="space-y-4">
            <p className="text-sm text-gray-400">
              {createStudentFor === 'match'
                ? 'Create a new student and assign both the current face and the selected similar face to them.'
                : 'Create a new student and assign the current face to them.'}
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-400 mb-1">First Name</label>
                <input
                  type="text"
                  value={newStudentData.first_name}
                  onChange={(e) =>
                    setNewStudentData((prev) => ({ ...prev, first_name: e.target.value }))
                  }
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  placeholder="Student"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Last Name</label>
                <input
                  type="text"
                  value={newStudentData.last_name}
                  onChange={(e) =>
                    setNewStudentData((prev) => ({ ...prev, last_name: e.target.value }))
                  }
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  placeholder="#1"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Student ID (optional)</label>
                <input
                  type="text"
                  value={newStudentData.student_id}
                  onChange={(e) =>
                    setNewStudentData((prev) => ({ ...prev, student_id: e.target.value }))
                  }
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  placeholder="e.g., 123456"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Email (optional)</label>
                <input
                  type="email"
                  value={newStudentData.email}
                  onChange={(e) =>
                    setNewStudentData((prev) => ({ ...prev, email: e.target.value }))
                  }
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  placeholder="student@example.com"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                variant="secondary"
                onClick={() => setShowCreateStudentModal(false)}
                className="flex-1"
                disabled={processing}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateStudentSubmit}
                className="flex-1"
                disabled={processing || !newStudentData.first_name || !newStudentData.last_name}
              >
                {processing ? 'Creating...' : 'Create & Assign'}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Select Existing Student Modal */}
        <Modal
          isOpen={showSelectStudentModal}
          onClose={() => setShowSelectStudentModal(false)}
          title="Select Student"
          className="max-w-lg"
        >
          <div className="space-y-4">
            <p className="text-sm text-gray-400">
              Choose an existing student to assign to this face.
            </p>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={studentSearchQuery}
                onChange={(e) => setStudentSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                placeholder="Search by name or student ID..."
                autoFocus
              />
            </div>

            {/* Student List */}
            <div className="max-h-96 overflow-y-auto space-y-2">
              {filteredStudents.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">
                    {studentSearchQuery ? 'No students match your search' : 'No students available'}
                  </p>
                </div>
              ) : (
                filteredStudents.map((student) => (
                  <button
                    key={student.id}
                    onClick={() => handleAssignToStudent(student)}
                    disabled={processing}
                    className="w-full flex items-center gap-3 p-3 bg-dark-hover rounded-lg border border-dark-border hover:border-primary/50 transition-colors text-left disabled:opacity-50"
                  >
                    {/* Profile Picture */}
                    <div className="w-10 h-10 rounded-full bg-dark-border overflow-hidden flex-shrink-0">
                      {student.profile_picture ? (
                        <img
                          src={getImageUrl(student.profile_picture)}
                          alt={student.full_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-500">
                          <Users className="w-5 h-5" />
                        </div>
                      )}
                    </div>
                    {/* Student Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {student.full_name}
                      </p>
                      {student.student_id && (
                        <p className="text-xs text-gray-400">ID: {student.student_id}</p>
                      )}
                    </div>
                    <UserCheck className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  </button>
                ))
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                variant="secondary"
                onClick={() => setShowSelectStudentModal(false)}
                className="w-full"
                disabled={processing}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default ManualAssignmentPage;