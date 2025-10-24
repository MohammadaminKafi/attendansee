import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { classesAPI } from '@/services/api';
import { Button, Card, Modal, Input, LoadingSpinner } from '@/components/ui';
import { getErrorMessage } from '@/utils/helpers';
import { formatDateTime } from '@/utils/helpers';
import type { Class, CreateClassData, UpdateClassData } from '@/types';
import { Plus, Edit2, Trash2, Users, Calendar } from 'lucide-react';

export const ClassesPage: React.FC = () => {
  const navigate = useNavigate();
  const [classes, setClasses] = useState<Class[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedClass, setSelectedClass] = useState<Class | null>(null);

  // Form states
  const [formData, setFormData] = useState<CreateClassData>({
    name: '',
    description: '',
    is_active: true,
  });
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await classesAPI.getClasses();
      setClasses(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formData.name.trim()) {
      setFormError('Class name is required');
      return;
    }

    setIsSubmitting(true);

    try {
      await classesAPI.createClass(formData);
      setIsCreateModalOpen(false);
      resetForm();
      await fetchClasses();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!selectedClass) return;

    if (!formData.name.trim()) {
      setFormError('Class name is required');
      return;
    }

    setIsSubmitting(true);

    try {
      const updateData: UpdateClassData = {
        name: formData.name,
        description: formData.description,
        is_active: formData.is_active,
      };
      await classesAPI.updateClass(selectedClass.id, updateData);
      setIsEditModalOpen(false);
      setSelectedClass(null);
      resetForm();
      await fetchClasses();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedClass) return;

    setIsSubmitting(true);

    try {
      await classesAPI.deleteClass(selectedClass.id);
      setIsDeleteModalOpen(false);
      setSelectedClass(null);
      await fetchClasses();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const openCreateModal = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const openEditModal = (classItem: Class) => {
    setSelectedClass(classItem);
    setFormData({
      name: classItem.name,
      description: classItem.description,
      is_active: classItem.is_active,
    });
    setIsEditModalOpen(true);
  };

  const openDeleteModal = (classItem: Class) => {
    setSelectedClass(classItem);
    setFormError('');
    setIsDeleteModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      is_active: true,
    });
    setFormError('');
  };

  const closeModals = () => {
    setIsCreateModalOpen(false);
    setIsEditModalOpen(false);
    setIsDeleteModalOpen(false);
    setSelectedClass(null);
    resetForm();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold text-gray-100">My Classes</h1>
            <Button onClick={openCreateModal} variant="primary">
              <Plus size={20} className="mr-2 inline" />
              Create Class
            </Button>
          </div>
          <p className="text-gray-400">
            Manage your classes and track attendance
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-danger bg-opacity-10 border border-danger rounded-lg">
            <p className="text-danger">{error}</p>
          </div>
        )}

        {/* Classes Grid */}
        {classes.length === 0 ? (
          <Card className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Calendar size={64} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">No classes yet</p>
              <p className="text-sm mt-2">Create your first class to get started</p>
            </div>
            <Button onClick={openCreateModal} variant="primary" className="mt-4">
              <Plus size={20} className="mr-2 inline" />
              Create Your First Class
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classes.map((classItem) => (
              <Card 
                key={classItem.id} 
                className="hover:border-primary transition-colors cursor-pointer"
                onClick={() => navigate(`/classes/${classItem.id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-100 mb-1">
                      {classItem.name}
                    </h3>
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        classItem.is_active
                          ? 'bg-success bg-opacity-20 text-success'
                          : 'bg-gray-600 bg-opacity-20 text-gray-400'
                      }`}
                    >
                      {classItem.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => openEditModal(classItem)}
                      className="p-2 text-gray-400 hover:text-primary transition-colors"
                      title="Edit class"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => openDeleteModal(classItem)}
                      className="p-2 text-gray-400 hover:text-danger transition-colors"
                      title="Delete class"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                {classItem.description && (
                  <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                    {classItem.description}
                  </p>
                )}

                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <div className="flex items-center gap-1">
                    <Users size={16} />
                    <span>{classItem.student_count} students</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar size={16} />
                    <span>{classItem.session_count} sessions</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-dark-border text-xs text-gray-500">
                  Created {formatDateTime(classItem.created_at)}
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Create Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={closeModals}
          title="Create New Class"
        >
          <form onSubmit={handleCreate} className="space-y-4">
            {formError && (
              <div className="p-3 bg-danger bg-opacity-10 border border-danger rounded-lg">
                <p className="text-danger text-sm">{formError}</p>
              </div>
            )}

            <Input
              label="Class Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Computer Science 101"
              disabled={isSubmitting}
              required
            />

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description for the class"
                rows={3}
                className="input-field resize-none"
                disabled={isSubmitting}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active_create"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4 text-primary bg-dark-card border-dark-border rounded focus:ring-primary"
                disabled={isSubmitting}
              />
              <label htmlFor="is_active_create" className="text-sm text-gray-300">
                Active class
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={closeModals}
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                className="flex-1"
                isLoading={isSubmitting}
              >
                Create Class
              </Button>
            </div>
          </form>
        </Modal>

        {/* Edit Modal */}
        <Modal
          isOpen={isEditModalOpen}
          onClose={closeModals}
          title="Edit Class"
        >
          <form onSubmit={handleEdit} className="space-y-4">
            {formError && (
              <div className="p-3 bg-danger bg-opacity-10 border border-danger rounded-lg">
                <p className="text-danger text-sm">{formError}</p>
              </div>
            )}

            <Input
              label="Class Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Computer Science 101"
              disabled={isSubmitting}
              required
            />

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description for the class"
                rows={3}
                className="input-field resize-none"
                disabled={isSubmitting}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active_edit"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4 text-primary bg-dark-card border-dark-border rounded focus:ring-primary"
                disabled={isSubmitting}
              />
              <label htmlFor="is_active_edit" className="text-sm text-gray-300">
                Active class
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={closeModals}
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                className="flex-1"
                isLoading={isSubmitting}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>

        {/* Delete Modal */}
        <Modal
          isOpen={isDeleteModalOpen}
          onClose={closeModals}
          title="Delete Class"
        >
          <div className="space-y-4">
            {formError && (
              <div className="p-3 bg-danger bg-opacity-10 border border-danger rounded-lg">
                <p className="text-danger text-sm">{formError}</p>
              </div>
            )}

            <p className="text-gray-300">
              Are you sure you want to delete the class{' '}
              <span className="font-semibold text-gray-100">
                {selectedClass?.name}
              </span>
              ?
            </p>

            <div className="p-3 bg-warning bg-opacity-10 border border-warning rounded-lg">
              <p className="text-warning text-sm">
                This action cannot be undone. All students, sessions, and attendance
                records associated with this class will be permanently deleted.
              </p>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={closeModals}
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="danger"
                onClick={handleDelete}
                className="flex-1"
                isLoading={isSubmitting}
              >
                Delete Class
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};
