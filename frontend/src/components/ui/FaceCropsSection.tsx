import React, { useState } from 'react';
import { faceCropsAPI, studentsAPI } from '@/services/api';
import { FaceCropDetail, Student } from '@/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import {
  Trash2,
  UserPlus,
  UserX,
  Edit2,
  Save,
  X as XIcon,
  CheckCircle,
  AlertCircle,
  ArrowUpDown,
  Users,
  Grid3x3,
} from 'lucide-react';

type SortOption = 'identified-first' | 'unidentified-first' | 'name-asc' | 'name-desc' | 'created-desc';
type ViewMode = 'grid' | 'grouped';

interface FaceCropsSectionProps {
  faceCrops: FaceCropDetail[];
  students: Student[];
  onUpdate: () => void;
  title?: string;
  description?: string;
  showImageInfo?: boolean;
}

export const FaceCropsSection: React.FC<FaceCropsSectionProps> = ({
  faceCrops,
  students,
  onUpdate,
  title = 'Face Crops',
  description,
  showImageInfo = false,
}) => {
  // State
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('created-desc');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  // Modal states
  const [showDeleteCropModal, setShowDeleteCropModal] = useState(false);
  const [deletingCropId, setDeletingCropId] = useState<number | null>(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigningCropId, setAssigningCropId] = useState<number | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentSearchQuery, setStudentSearchQuery] = useState('');
  const [showEditStudentModal, setShowEditStudentModal] = useState(false);
  const [editingCropId, setEditingCropId] = useState<number | null>(null);
  const [editStudentData, setEditStudentData] = useState({
    first_name: '',
    last_name: '',
    student_id: '',
  });

  // Helper functions
  const getImageUrl = (path: string) => {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  };

  const sortFaceCrops = (crops: FaceCropDetail[]): FaceCropDetail[] => {
    const sorted = [...crops];
    switch (sortBy) {
      case 'identified-first':
        return sorted.sort((a, b) => Number(b.is_identified) - Number(a.is_identified));
      case 'unidentified-first':
        return sorted.sort((a, b) => Number(a.is_identified) - Number(b.is_identified));
      case 'name-asc':
        return sorted.sort((a, b) => {
          if (!a.student_name) return 1;
          if (!b.student_name) return -1;
          return a.student_name.localeCompare(b.student_name);
        });
      case 'name-desc':
        return sorted.sort((a, b) => {
          if (!a.student_name) return 1;
          if (!b.student_name) return -1;
          return b.student_name.localeCompare(a.student_name);
        });
      case 'created-desc':
      default:
        return sorted.sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
    }
  };

  const groupByStudent = (crops: FaceCropDetail[]) => {
    const grouped: { [key: string]: FaceCropDetail[] } = {
      unidentified: [],
    };

    crops.forEach((crop) => {
      if (crop.is_identified && crop.student_name) {
        if (!grouped[crop.student_name]) {
          grouped[crop.student_name] = [];
        }
        grouped[crop.student_name].push(crop);
      } else {
        grouped.unidentified.push(crop);
      }
    });

    return grouped;
  };

  // Handlers
  const handleAssignStudent = async () => {
    if (!assigningCropId || !selectedStudentId) return;

    try {
      await faceCropsAPI.updateFaceCrop(assigningCropId, {
        student: selectedStudentId,
      });

      setShowAssignModal(false);
      setAssigningCropId(null);
      setSelectedStudentId(null);
      setStudentSearchQuery('');
      onUpdate();
    } catch (err) {
      console.error('Error assigning student:', err);
      setError('Failed to assign student');
    }
  };

  const handleUnassignStudent = async (cropId: number) => {
    try {
      await faceCropsAPI.unidentifyFaceCrop(cropId);
      onUpdate();
    } catch (err) {
      console.error('Error unassigning student:', err);
      setError('Failed to unassign student');
    }
  };

  const handleDeleteCrop = async () => {
    if (!deletingCropId) return;

    try {
      await faceCropsAPI.deleteFaceCrop(deletingCropId);
      setShowDeleteCropModal(false);
      setDeletingCropId(null);
      onUpdate();
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
      await studentsAPI.updateStudent(crop.student, editStudentData);
      setShowEditStudentModal(false);
      setEditingCropId(null);
      onUpdate();
    } catch (err) {
      console.error('Error updating student:', err);
      setError('Failed to update student information');
    }
  };

  // Render helpers
  const renderCropCard = (crop: FaceCropDetail, showImage: boolean = false) => (
    <div
      key={crop.id}
      className="relative group bg-dark-card rounded-lg overflow-hidden border border-dark-border hover:border-primary transition-colors"
    >
      {/* Face Crop Image */}
      <div className="aspect-square bg-dark-bg flex items-center justify-center">
        <img
          src={getImageUrl(crop.crop_image_path)}
          alt={`Face ${crop.id}`}
          className="w-full h-full object-cover"
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
            <p className="text-sm text-white font-medium truncate">{crop.student_name}</p>
            {showImage && crop.image_id && (
              <p className="text-xs text-gray-500 mt-1">Image #{crop.image_id}</p>
            )}
          </div>
        ) : (
          <div>
            <Badge variant="warning" className="text-xs mb-2">
              <AlertCircle className="w-3 h-3 mr-1" />
              Unidentified
            </Badge>
            <p className="text-xs text-gray-500">No student assigned</p>
            {showImage && crop.image_id && (
              <p className="text-xs text-gray-500 mt-1">Image #{crop.image_id}</p>
            )}
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
              onClick={() => openEditStudentModal(crop)}
              className="w-full"
            >
              <Edit2 className="w-3 h-3 mr-1" />
              Edit Info
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleUnassignStudent(crop.id)}
              className="w-full"
            >
              <UserX className="w-3 h-3 mr-1" />
              Unassign
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            onClick={() => {
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
          onClick={() => {
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
  );

  const sortedCrops = sortFaceCrops(faceCrops);
  const groupedCrops = viewMode === 'grouped' ? groupByStudent(sortedCrops) : null;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-white">{title}</h2>
          {description && <p className="text-sm text-gray-400 mt-1">{description}</p>}
          <p className="text-sm text-gray-400 mt-1">
            {faceCrops.length} face{faceCrops.length !== 1 ? 's' : ''} detected •{' '}
            {faceCrops.filter((c) => c.is_identified).length} identified
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 bg-dark-hover rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'grid'
                  ? 'bg-primary text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
              title="Grid view"
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grouped')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'grouped'
                  ? 'bg-primary text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
              title="Grouped by student"
            >
              <Users className="w-4 h-4" />
            </button>
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="appearance-none bg-dark-hover border border-dark-border rounded-lg px-4 py-2 pr-10 text-sm text-white focus:outline-none focus:border-primary cursor-pointer"
            >
              <option value="created-desc">Recently Added</option>
              <option value="identified-first">Identified First</option>
              <option value="unidentified-first">Unidentified First</option>
              <option value="name-asc">Name (A-Z)</option>
              <option value="name-desc">Name (Z-A)</option>
            </select>
            <ArrowUpDown className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-danger-light flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-danger-light">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-danger-light hover:text-danger">
            <XIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Face Crops Display */}
      {faceCrops.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-dark-border rounded-lg">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400 mb-2">No face crops yet</p>
          <p className="text-sm text-gray-500">Process images to detect faces</p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {sortedCrops.map((crop) => renderCropCard(crop, showImageInfo))}
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedCrops!).map(([studentName, crops]) => (
            <div key={studentName} className="bg-dark-hover rounded-lg p-4 border border-dark-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  {studentName === 'unidentified' ? (
                    <span className="text-gray-400">Unidentified Faces</span>
                  ) : (
                    studentName
                  )}
                </h3>
                <Badge variant={studentName === 'unidentified' ? 'warning' : 'success'}>
                  {crops.length} crop{crops.length !== 1 ? 's' : ''}
                </Badge>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {crops.map((crop) => renderCropCard(crop, showImageInfo))}
              </div>
            </div>
          ))}
        </div>
      )}

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
                  {student.email && <p className="text-xs text-gray-400">{student.email}</p>}
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
              {studentSearchQuery
                ? 'No students found matching your search.'
                : 'No students available. Add students to the class first.'}
            </p>
          )}

          <div className="flex gap-3 pt-4">
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
            <Button onClick={handleAssignStudent} disabled={!selectedStudentId} className="flex-1">
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
            <label className="block text-sm font-medium text-gray-300 mb-2">First Name</label>
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
            <label className="block text-sm font-medium text-gray-300 mb-2">Last Name</label>
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
            <label className="block text-sm font-medium text-gray-300 mb-2">Student ID</label>
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
          <p className="text-gray-300">Are you sure you want to delete this face crop?</p>

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
