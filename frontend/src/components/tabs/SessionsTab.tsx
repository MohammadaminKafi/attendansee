import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit2, Trash2 } from 'lucide-react';
import { sessionsAPI } from '@/services/api';
import { Session, CreateSessionData, UpdateSessionData } from '@/types';
import { Table, Column } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface SessionsTabProps {
  classId: number;
  onUpdate?: () => void;
}

const ITEMS_PER_PAGE = 10;

export const SessionsTab: React.FC<SessionsTabProps> = ({ classId, onUpdate }) => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filteredSessions, setFilteredSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingSession, setEditingSession] = useState<Session | null>(null);
  const [deletingSession, setDeletingSession] = useState<Session | null>(null);
  const [formData, setFormData] = useState<CreateSessionData>({
    name: '',
    date: '',
    start_time: '',
    end_time: '',
    notes: '',
    class_session: classId,
  });
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadSessions();
  }, [classId]);

  useEffect(() => {
    // Filter sessions based on search query
    if (searchQuery) {
      const filtered = sessions.filter(
        (session) =>
          session.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          session.date.includes(searchQuery)
      );
      setFilteredSessions(filtered);
    } else {
      setFilteredSessions(sessions);
    }
    setCurrentPage(1); // Reset to first page when search changes
  }, [searchQuery, sessions]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const data = await sessionsAPI.getSessions(classId);
      setSessions(data);
      setFilteredSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickCreate = async () => {
    try {
      // Generate auto name: "Session {count + 1}"
      const sessionNumber = sessions.length + 1;
      const autoName = `Session ${sessionNumber}`;
      
      // Use today's date in YYYY-MM-DD format
      const today = new Date().toISOString().split('T')[0];
      
      await sessionsAPI.createSession({
        class_session: classId,
        name: autoName,
        date: today,
      });
      
      await loadSessions();
      onUpdate?.();
    } catch (error: any) {
      console.error('Failed to create session:', error);
      alert(error.response?.data?.detail || 'Failed to create session');
    }
  };

  const handleEdit = (session: Session) => {
    setEditingSession(session);
    setFormData({
      name: session.name,
      date: session.date,
      start_time: session.start_time || '',
      end_time: session.end_time || '',
      notes: session.notes || '',
      class_session: classId,
    });
    setShowModal(true);
  };

  const openDeleteModal = (session: Session) => {
    setDeletingSession(session);
    setFormError('');
    setShowDeleteModal(true);
  };

  const handleDelete = async () => {
    if (!deletingSession) return;

    setIsSubmitting(true);
    setFormError('');

    try {
      await sessionsAPI.deleteSession(deletingSession.id);
      setShowDeleteModal(false);
      setDeletingSession(null);
      await loadSessions();
      onUpdate?.();
    } catch (error: any) {
      console.error('Failed to delete session:', error);
      setFormError(error.response?.data?.detail || 'Failed to delete session');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!editingSession) return;

    try {
      await sessionsAPI.updateSession(editingSession.id, formData as UpdateSessionData);
      setShowModal(false);
      await loadSessions();
      onUpdate?.();
    } catch (error: any) {
      console.error('Failed to update session:', error);
      alert(error.response?.data?.detail || 'Failed to update session');
    }
  };

  // Pagination
  const totalPages = Math.ceil(filteredSessions.length / ITEMS_PER_PAGE);
  const paginatedSessions = filteredSessions.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const columns: Column<Session>[] = [
    {
      key: 'date',
      header: 'Date',
      width: '15%',
      render: (session) => new Date(session.date).toLocaleDateString(),
    },
    {
      key: 'name',
      header: 'Name',
      width: '35%',
      render: (session) => (
        <div className="flex items-center justify-between group">
          <span>{session.name}</span>
          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleEdit(session);
              }}
              className="p-1 hover:bg-dark-hover rounded text-gray-400 hover:text-primary transition-colors"
              title="Edit session"
            >
              <Edit2 size={16} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                openDeleteModal(session);
              }}
              className="p-1 hover:bg-dark-hover rounded text-gray-400 hover:text-danger transition-colors"
              title="Delete session"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      ),
    },
    {
      key: 'image_count',
      header: 'Images',
      width: '10%',
      render: (session) => session.image_count || 0,
    },
    {
      key: 'face_crop_count',
      header: 'Faces',
      width: '10%',
      render: (session) => session.total_faces_count || 0,
    },
    {
      key: 'is_processed',
      header: 'Status',
      width: '15%',
      render: (session) => (
        <Badge variant={session.is_processed ? 'success' : 'warning'}>
          {session.is_processed ? 'Processed' : 'Pending'}
        </Badge>
      ),
    },
  ];

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
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button onClick={handleQuickCreate}>+ Create Session</Button>
      </div>

      {/* Table */}
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <Table
          data={paginatedSessions}
          columns={columns}
          keyExtractor={(session) => session.id}
          emptyMessage="No sessions found"
          onRowClick={(session) => navigate(`/classes/${classId}/sessions/${session.id}`)}
        />
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          className="mt-6"
        />
      )}

      {/* Edit Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Edit Session"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Session Name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Morning Session"
          />
          <Input
            label="Date (Optional)"
            type="date"
            value={formData.date}
            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Start Time"
              type="time"
              value={formData.start_time}
              onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
            />
            <Input
              label="End Time"
              type="time"
              value={formData.end_time}
              onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes (Optional)
            </label>
            <textarea
              className="w-full px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Add any additional notes..."
            />
          </div>
          <div className="flex gap-3 justify-end pt-4">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button type="submit">Update</Button>
          </div>
        </form>
      </Modal>

      {/* Delete Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Session"
      >
        <div className="space-y-4">
          {formError && (
            <div className="p-3 bg-danger bg-opacity-10 border border-danger rounded-lg">
              <p className="text-danger text-sm">{formError}</p>
            </div>
          )}

          <p className="text-gray-300">
            Are you sure you want to delete the session{' '}
            <span className="font-semibold text-gray-100">
              {deletingSession?.name}
            </span>
            ?
          </p>

          <div className="p-3 bg-warning bg-opacity-10 border border-warning rounded-lg">
            <p className="text-warning text-sm">
              This action cannot be undone. All images and attendance data
              associated with this session will be permanently deleted.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowDeleteModal(false)}
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
              Delete Session
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
