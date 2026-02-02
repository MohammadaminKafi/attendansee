import React, { useState, useEffect } from 'react';
import { classesAPI } from '@/services/api';
import { Class } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Save, Edit2 } from 'lucide-react';

interface NotesTabProps {
  classId: number;
  onUpdate?: () => void;
}

export const NotesTab: React.FC<NotesTabProps> = ({ classId, onUpdate }) => {
  const [classData, setClassData] = useState<Class | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    loadClassData();
  }, [classId]);

  const loadClassData = async () => {
    try {
      setLoading(true);
      const data = await classesAPI.getClass(classId);
      setClassData(data);
      setNotes(data.notes || '');
    } catch (err) {
      console.error('Failed to load class data:', err);
      setError('Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccessMessage('');
      
      await classesAPI.updateClass(classId, { notes });
      
      setSuccessMessage('Notes saved successfully!');
      setEditing(false);
      onUpdate?.();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      console.error('Failed to save notes:', err);
      setError(err.response?.data?.detail || 'Failed to save notes');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setNotes(classData?.notes || '');
    setEditing(false);
    setError('');
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Class Notes</h2>
          <p className="text-sm text-gray-400 mt-1">
            Add notes, reminders, or any additional information about this class
          </p>
        </div>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <Button
                onClick={handleCancel}
                variant="secondary"
                size="sm"
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                variant="primary"
                size="sm"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button
              onClick={() => setEditing(true)}
              variant="primary"
              size="sm"
            >
              <Edit2 className="w-4 h-4 mr-2" />
              Edit
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-danger/10 border border-danger rounded-lg">
          <p className="text-danger text-sm">{error}</p>
        </div>
      )}

      {successMessage && (
        <div className="p-3 bg-success/10 border border-success rounded-lg">
          <p className="text-success text-sm">{successMessage}</p>
        </div>
      )}

      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        {editing ? (
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add your notes here..."
            className="w-full h-96 px-4 py-3 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
          />
        ) : (
          <div className="min-h-[24rem] text-gray-300 whitespace-pre-wrap">
            {notes || (
              <p className="text-gray-500 italic">
                No notes yet. Click "Edit" to add notes.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
