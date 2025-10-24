import React, { useState, useEffect } from 'react';
import { studentsAPI } from '@/services/api';
import { Student, CreateStudentData, UpdateStudentData } from '@/types';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface StudentsTabProps {
  classId: number;
  onUpdate?: () => void;
}

export const StudentsTab: React.FC<StudentsTabProps> = ({ classId, onUpdate }) => {
  const [students, setStudents] = useState<Student[]>([]);
  const [filteredStudents, setFilteredStudents] = useState<Student[]>([]);
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
      const data = await studentsAPI.getStudents(classId);
      setStudents(data);
      setFilteredStudents(data);
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
      if (editingStudent) {
        await studentsAPI.updateStudent(editingStudent.id, formData as UpdateStudentData);
      } else {
        await studentsAPI.createStudent(formData);
      }
      setShowModal(false);
      await loadStudents();
      onUpdate?.();
    } catch (error: any) {
      console.error('Failed to save student:', error);
      alert(error.response?.data?.detail || 'Failed to save student');
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
          <Button variant="secondary" onClick={() => setShowUploadModal(true)}>
            📤 Upload CSV
          </Button>
          <Button onClick={handleCreate}>+ Add Student</Button>
        </div>
      </div>

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
              className="bg-dark-card border border-dark-border rounded-lg p-4 hover:border-primary transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-100">
                    {student.first_name} {student.last_name}
                  </h3>
                  <div className="flex gap-4 mt-1 text-sm text-gray-400">
                    <span>ID: {student.student_id}</span>
                    {student.email && <span>Email: {student.email}</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => handleEdit(student)}>
                    Edit
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => handleDelete(student)}>
                    Delete
                  </Button>
                </div>
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
            <Button type="submit">{editingStudent ? 'Update' : 'Add'}</Button>
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
    </div>
  );
};
