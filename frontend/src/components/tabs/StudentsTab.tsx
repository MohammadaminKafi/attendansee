import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { studentsAPI, sessionsAPI } from '@/services/api';
import { Student, CreateStudentData, UpdateStudentData } from '@/types';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Eye, Edit2, Trash2, GitMerge, X, User, Upload as UploadIcon, XCircle } from 'lucide-react';

interface StudentsTabProps {
  classId: number;
  onUpdate?: () => void;
}

interface StudentWithAttendance extends Student {
  attended_sessions?: number;
  total_sessions?: number;
}

export const StudentsTab: React.FC<StudentsTabProps> = ({ classId, onUpdate }) => {
  const navigate = useNavigate();
  const profilePictureInputRef = useRef<HTMLInputElement>(null);
  const [students, setStudents] = useState<StudentWithAttendance[]>([]);
  const [filteredStudents, setFilteredStudents] = useState<StudentWithAttendance[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [formData, setFormData] = useState<CreateStudentData>({
    first_name: '',
    last_name: '',
    student_id: '',
    email: '',
    class_enrolled: classId,
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [hasHeader, setHasHeader] = useState(true);
  const [uploadResult, setUploadResult] = useState<any>(null);
  
  // Profile picture state
  const [profilePictureFile, setProfilePictureFile] = useState<File | null>(null);
  const [profilePicturePreview, setProfilePicturePreview] = useState<string | null>(null);
  const [uploadingProfilePicture, setUploadingProfilePicture] = useState(false);
  
  // Merge functionality state
  const [mergeMode, setMergeMode] = useState(false);
  const [sourceStudentForMerge, setSourceStudentForMerge] = useState<Student | null>(null);
  const [showMergeConfirmModal, setShowMergeConfirmModal] = useState(false);
  const [selectedTargetStudent, setSelectedTargetStudent] = useState<Student | null>(null);
  const [merging, setMerging] = useState(false);

  useEffect(() => {
    loadStudents();
  }, [classId]);

  useEffect(() => {
    // Filter students based on search query
    if (searchQuery) {
      const filtered = students.filter(
        (student) =>
          student.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          student.last_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          student.student_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          student.email?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredStudents(filtered);
    } else {
      setFilteredStudents(students);
    }
  }, [searchQuery, students]);

  const loadStudents = async () => {
    try {
      setLoading(true);
      
      // Fetch students and sessions in parallel
      const [studentsData, sessionsData] = await Promise.all([
        studentsAPI.getStudents(classId),
        sessionsAPI.getSessions(classId),
      ]);
      
      // Fetch attendance for each student
      const studentsWithAttendance = await Promise.all(
        studentsData.map(async (student) => {
          try {
            // Count sessions where student was present
            sessionsData.filter(() =>
              // This is a simplified check - in reality we'd need to query face crops
              // But we'll do a simple calculation here
              false // Will be updated when we have the attendance data
            ).length;
            
            return {
              ...student,
              attended_sessions: 0, // Will be calculated properly in backend
              total_sessions: sessionsData.length,
            };
          } catch {
            return {
              ...student,
              attended_sessions: 0,
              total_sessions: sessionsData.length,
            };
          }
        })
      );
      
      setStudents(studentsWithAttendance);
      setFilteredStudents(studentsWithAttendance);
    } catch (error) {
      console.error('Failed to load students:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingStudent(null);
    setFormData({
      first_name: '',
      last_name: '',
      student_id: '',
      email: '',
      class_enrolled: classId,
    });
    setProfilePictureFile(null);
    setProfilePicturePreview(null);
    setShowModal(true);
  };

  const handleEdit = (student: Student) => {
    setEditingStudent(student);
    setFormData({
      first_name: student.first_name,
      last_name: student.last_name,
      student_id: student.student_id,
      email: student.email || '',
      class_enrolled: classId,
    });
    setProfilePictureFile(null);
    setProfilePicturePreview(student.profile_picture);
    setShowModal(true);
  };

  const handleDelete = async (student: Student) => {
    if (
      !confirm(
        `Are you sure you want to delete student "${student.first_name} ${student.last_name}"?`
      )
    ) {
      return;
    }

    try {
      await studentsAPI.deleteStudent(student.id);
      await loadStudents();
      onUpdate?.();
    } catch (error) {
      console.error('Failed to delete student:', error);
      alert('Failed to delete student');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      let savedStudent: Student;
      
      if (editingStudent) {
        savedStudent = await studentsAPI.updateStudent(editingStudent.id, formData as UpdateStudentData);
      } else {
        savedStudent = await studentsAPI.createStudent(formData);
      }
      
      // Upload profile picture if a new file was selected
      if (profilePictureFile && savedStudent.id) {
        try {
          setUploadingProfilePicture(true);
          await studentsAPI.uploadProfilePicture(savedStudent.id, profilePictureFile);
        } catch (uploadError) {
          console.error('Failed to upload profile picture:', uploadError);
          alert('Student saved but failed to upload profile picture');
        } finally {
          setUploadingProfilePicture(false);
        }
      }
      
      setShowModal(false);
      setProfilePictureFile(null);
      setProfilePicturePreview(null);
      await loadStudents();
      onUpdate?.();
    } catch (error: any) {
      console.error('Failed to save student:', error);
      alert(error.response?.data?.detail || 'Failed to save student');
    }
  };
  
  const handleProfilePictureSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size too large. Maximum size is 5MB.');
      return;
    }
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Invalid file type. Please upload an image file.');
      return;
    }
    
    setProfilePictureFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setProfilePicturePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };
  
  const handleRemoveProfilePicture = async () => {
    if (editingStudent?.profile_picture) {
      // If editing and has existing picture, delete from server
      try {
        setUploadingProfilePicture(true);
        await studentsAPI.deleteProfilePicture(editingStudent.id);
        setProfilePicturePreview(null);
        setProfilePictureFile(null);
        await loadStudents();
        // Update editingStudent state
        setEditingStudent({ ...editingStudent, profile_picture: null });
      } catch (error) {
        console.error('Failed to delete profile picture:', error);
        alert('Failed to delete profile picture');
      } finally {
        setUploadingProfilePicture(false);
      }
    } else {
      // Just clear the preview if it's a new upload
      setProfilePicturePreview(null);
      setProfilePictureFile(null);
      if (profilePictureInputRef.current) {
        profilePictureInputRef.current.value = '';
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
      setUploadResult(null);
    }
  };

  const handleBulkUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!uploadFile) {
      alert('Please select a CSV file');
      return;
    }

    try {
      const result = await studentsAPI.bulkUploadStudents(classId, uploadFile, hasHeader);
      setUploadResult(result);
      await loadStudents();
      onUpdate?.();
    } catch (error: any) {
      console.error('Failed to upload students:', error);
      alert(error.response?.data?.detail || 'Failed to upload students');
    }
  };

  const closeUploadModal = () => {
    setShowUploadModal(false);
    setUploadFile(null);
    setUploadResult(null);
    setHasHeader(true);
  };

  const startMerge = (student: Student) => {
    setMergeMode(true);
    setSourceStudentForMerge(student);
  };

  const cancelMerge = () => {
    setMergeMode(false);
    setSourceStudentForMerge(null);
    setSelectedTargetStudent(null);
    setShowMergeConfirmModal(false);
  };

  const selectTargetForMerge = (targetStudent: Student) => {
    if (sourceStudentForMerge && targetStudent.id !== sourceStudentForMerge.id) {
      setSelectedTargetStudent(targetStudent);
      setShowMergeConfirmModal(true);
    }
  };

  const confirmMerge = async () => {
    if (!sourceStudentForMerge || !selectedTargetStudent) return;

    setMerging(true);
    try {
      await studentsAPI.mergeStudents(sourceStudentForMerge.id, {
        target_student_id: selectedTargetStudent.id,
      });

      // Show success message
      alert(
        `Successfully merged "${sourceStudentForMerge.first_name} ${sourceStudentForMerge.last_name}" into "${selectedTargetStudent.first_name} ${selectedTargetStudent.last_name}"`
      );

      // Reload students and reset merge state
      await loadStudents();
      onUpdate?.();
      cancelMerge();
    } catch (error: any) {
      console.error('Failed to merge students:', error);
      alert(error.response?.data?.detail || error.response?.data?.error || 'Failed to merge students');
    } finally {
      setMerging(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1 max-w-md">
          <Input
            type="text"
            placeholder="Search students by name, ID, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex gap-3">
          {mergeMode ? (
            <Button variant="secondary" onClick={cancelMerge}>
              <X className="w-4 h-4 mr-1" />
              Cancel Merge
            </Button>
          ) : (
            <>
              <Button variant="secondary" onClick={() => setShowUploadModal(true)}>
                📤 Upload CSV
              </Button>
              <Button onClick={handleCreate}>+ Add Student</Button>
            </>
          )}
        </div>
      </div>

      {/* Merge Mode Info Banner */}
      {mergeMode && sourceStudentForMerge && (
        <div className="mb-6 p-4 bg-primary bg-opacity-10 border border-primary rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-primary font-semibold mb-1">Merge Mode Active</h3>
              <p className="text-gray-300 text-sm">
                Merging: <span className="font-semibold">{sourceStudentForMerge.full_name}</span>
              </p>
              <p className="text-gray-400 text-xs mt-1">
                Click on another student to select merge target
              </p>
            </div>
            <button
              onClick={cancelMerge}
              className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>
      )}

      {/* Student List */}
      <div className="grid gap-4">
        {filteredStudents.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p>No students found</p>
          </div>
        ) : (
          filteredStudents.map((student) => (
            <div
              key={student.id}
              className={`bg-dark-card border rounded-lg p-4 transition-colors ${
                mergeMode
                  ? sourceStudentForMerge?.id === student.id
                    ? 'border-primary bg-primary bg-opacity-5'
                    : 'border-dark-border hover:border-success cursor-pointer'
                  : 'border-dark-border hover:border-primary cursor-pointer'
              }`}
              onClick={() => {
                if (mergeMode && sourceStudentForMerge?.id !== student.id) {
                  selectTargetForMerge(student);
                } else if (!mergeMode) {
                  navigate(`/classes/${classId}/students/${student.id}`);
                }
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  {/* Profile Picture */}
                  <div className="w-12 h-12 rounded-full overflow-hidden bg-dark-hover flex-shrink-0 border-2 border-dark-border">
                    {student.profile_picture ? (
                      <img
                        src={student.profile_picture}
                        alt={student.full_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <User size={24} />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <h3 className={`text-lg font-semibold transition-colors ${
                      mergeMode && sourceStudentForMerge?.id !== student.id
                        ? 'text-success'
                        : 'text-gray-100 group-hover:text-primary'
                    }`}>
                      {student.first_name} {student.last_name}
                      {mergeMode && sourceStudentForMerge?.id === student.id && (
                        <span className="ml-2 text-xs text-primary">(Source)</span>
                      )}
                    </h3>
                    <div className="flex gap-4 mt-1 text-sm text-gray-400">
                      <span>ID: {student.student_id}</span>
                      {student.email && <span>Email: {student.email}</span>}
                      {student.total_sessions !== undefined && (
                        <span className="text-primary font-medium">
                          Attendance: {student.attended_sessions || 0}/{student.total_sessions}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                {!mergeMode && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/classes/${classId}/students/${student.id}`);
                      }}
                      className="p-2 hover:bg-dark-hover rounded text-gray-400 hover:text-primary transition-colors"
                      title="View student"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startMerge(student);
                      }}
                      className="p-2 hover:bg-dark-hover rounded text-gray-400 hover:text-success transition-colors"
                      title="Merge student"
                    >
                      <GitMerge size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(student);
                      }}
                      className="p-2 hover:bg-dark-hover rounded text-gray-400 hover:text-primary transition-colors"
                      title="Edit student"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(student);
                      }}
                      className="p-2 hover:bg-dark-hover rounded text-gray-400 hover:text-danger transition-colors"
                      title="Delete student"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add/Edit Student Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingStudent ? 'Edit Student' : 'Add Student'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Profile Picture Section */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Profile Picture (Optional)
            </label>
            <div className="flex items-center gap-4">
              {/* Preview */}
              <div className="w-20 h-20 rounded-full overflow-hidden bg-dark-hover flex-shrink-0 border-2 border-dark-border">
                {profilePicturePreview ? (
                  <img
                    src={profilePicturePreview}
                    alt="Profile preview"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <User size={32} />
                  </div>
                )}
              </div>
              
              {/* Upload/Delete Controls */}
              <div className="flex flex-col gap-2">
                <input
                  ref={profilePictureInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleProfilePictureSelect}
                  className="hidden"
                  disabled={uploadingProfilePicture}
                />
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => profilePictureInputRef.current?.click()}
                  disabled={uploadingProfilePicture}
                >
                  <UploadIcon className="w-4 h-4 mr-2" />
                  {profilePicturePreview ? 'Change Picture' : 'Upload Picture'}
                </Button>
                {profilePicturePreview && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={handleRemoveProfilePicture}
                    disabled={uploadingProfilePicture}
                    className="text-danger hover:text-danger"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Remove Picture
                  </Button>
                )}
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Accepted formats: JPEG, PNG, GIF, WebP. Max size: 5MB
            </p>
          </div>
          
          <Input
            label="First Name"
            required
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            placeholder="John"
          />
          <Input
            label="Last Name"
            required
            value={formData.last_name}
            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            placeholder="Doe"
          />
          <Input
            label="Student ID (Optional)"
            value={formData.student_id}
            onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
            placeholder="2024001"
          />
          <Input
            label="Email (Optional)"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="john.doe@example.com"
          />
          <div className="flex gap-3 justify-end pt-4">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={uploadingProfilePicture}>
              {uploadingProfilePicture ? 'Uploading...' : editingStudent ? 'Update' : 'Add'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* CSV Upload Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={closeUploadModal}
        title="Upload Students via CSV"
      >
        <form onSubmit={handleBulkUpload} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">CSV File</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
            <p className="mt-2 text-xs text-gray-400">
              CSV should contain: first_name, last_name, student_id, email (optional)
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="hasHeader"
              checked={hasHeader}
              onChange={(e) => setHasHeader(e.target.checked)}
              className="w-4 h-4 text-primary bg-dark-card border-dark-border rounded focus:ring-primary"
            />
            <label htmlFor="hasHeader" className="text-sm text-gray-300">
              CSV file has header row
            </label>
          </div>

          {uploadResult && (
            <div className="p-4 bg-dark-hover rounded-lg">
              <p className="text-success font-medium mb-2">{uploadResult.message}</p>
              <div className="text-sm text-gray-300">
                <p>✓ Created: {uploadResult.total_created}</p>
                {uploadResult.total_skipped > 0 && (
                  <>
                    <p className="text-warning mt-2">⚠ Skipped: {uploadResult.total_skipped}</p>
                    <div className="mt-2 max-h-40 overflow-y-auto">
                      {uploadResult.skipped.map((item: any, index: number) => (
                        <p key={index} className="text-xs text-gray-400">
                          {item.first_name} {item.last_name} ({item.student_id}): {item.reason}
                        </p>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          <div className="flex gap-3 justify-end pt-4">
            <Button type="button" variant="secondary" onClick={closeUploadModal}>
              {uploadResult ? 'Close' : 'Cancel'}
            </Button>
            {!uploadResult && <Button type="submit">Upload</Button>}
          </div>
        </form>
      </Modal>

      {/* Merge Confirmation Modal */}
      <Modal
        isOpen={showMergeConfirmModal}
        onClose={() => !merging && setShowMergeConfirmModal(false)}
        title="Confirm Student Merge"
      >
        <div className="space-y-4">
          <div className="p-4 bg-warning bg-opacity-10 border border-warning rounded-lg">
            <p className="text-warning font-medium mb-2">⚠️ Warning: This action cannot be undone</p>
            <p className="text-gray-300 text-sm">
              The source student will be permanently deleted after merging.
            </p>
          </div>

          {sourceStudentForMerge && selectedTargetStudent && (
            <div className="space-y-3">
              <div className="p-3 bg-dark-hover rounded-lg">
                <p className="text-xs text-gray-400 mb-1">Source Student (will be deleted):</p>
                <p className="text-danger font-semibold">
                  {sourceStudentForMerge.full_name}
                  {sourceStudentForMerge.student_id && ` (${sourceStudentForMerge.student_id})`}
                </p>
              </div>

              <div className="flex justify-center">
                <div className="text-gray-400">↓</div>
              </div>

              <div className="p-3 bg-dark-hover rounded-lg">
                <p className="text-xs text-gray-400 mb-1">Target Student (will be kept):</p>
                <p className="text-success font-semibold">
                  {selectedTargetStudent.full_name}
                  {selectedTargetStudent.student_id && ` (${selectedTargetStudent.student_id})`}
                </p>
              </div>

              <div className="p-3 bg-dark-card border border-dark-border rounded-lg">
                <p className="text-gray-300 text-sm">
                  All face crops from <span className="font-semibold">{sourceStudentForMerge.full_name}</span> will be transferred to{' '}
                  <span className="font-semibold">{selectedTargetStudent.full_name}</span>, and then{' '}
                  <span className="font-semibold">{sourceStudentForMerge.full_name}</span> will be deleted.
                </p>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowMergeConfirmModal(false)}
              className="flex-1"
              disabled={merging}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={confirmMerge}
              className="flex-1"
              isLoading={merging}
            >
              Merge Students
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
