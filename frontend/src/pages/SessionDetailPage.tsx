import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { sessionsAPI, imagesAPI, classesAPI } from '@/services/api';
import { Session, Image, Class } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Upload, Trash2, Clock, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';

const SessionDetailPage: React.FC = () => {
  const { classId, sessionId } = useParams<{ classId: string; sessionId: string }>();
  const navigate = useNavigate();
  
  const [session, setSession] = useState<Session | null>(null);
  const [classData, setClassData] = useState<Class | null>(null);
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteImageModal, setShowDeleteImageModal] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, [classId, sessionId]);

  const loadData = async () => {
    if (!classId || !sessionId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const [sessionData, classInfo, imagesData] = await Promise.all([
        sessionsAPI.getSession(parseInt(sessionId)),
        classesAPI.getClass(parseInt(classId)),
        imagesAPI.getImages(parseInt(sessionId))
      ]);
      
      setSession(sessionData);
      setClassData(classInfo);
      setImages(imagesData);
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
    // If path is already a full URL, return it
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    // Otherwise, construct URL from API base
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    // Remove '/api' from the end if present
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
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
      {/* Back Button */}
      <button
        onClick={() => navigate(`/classes/${classId}`)}
        className="group flex items-center gap-2 text-gray-400 hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-medium">Back to Class</span>
      </button>

      <Breadcrumb items={breadcrumbItems} />

      {/* Session Header */}
      <Card className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{session.name}</h1>
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
          <div className="mt-4 p-4 bg-dark-hover rounded-lg border border-dark-border">
            <p className="text-sm text-gray-300">{session.notes}</p>
          </div>
        )}

        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border hover:border-primary transition-colors">
            <p className="text-sm text-gray-400">Images</p>
            <p className="text-2xl font-bold text-white">{images.length}</p>
          </div>
          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border hover:border-primary transition-colors">
            <p className="text-sm text-gray-400">Total Faces</p>
            <p className="text-2xl font-bold text-white">{session.total_faces_count}</p>
          </div>
          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border hover:border-primary transition-colors">
            <p className="text-sm text-gray-400">Identified</p>
            <p className="text-2xl font-bold text-white">{session.identified_faces_count}</p>
          </div>
        </div>
      </Card>

      {/* Upload Section */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Images</h2>
            <p className="text-sm text-gray-400 mt-1">
              {images.length} / 20 images uploaded
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
                {/* Image Preview */}
                <div className="aspect-square bg-dark-bg flex items-center justify-center">
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
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="absolute bottom-0 left-0 right-0 p-3">
                    <div className="flex items-center justify-between mb-2">
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
                      <button
                        onClick={() => openDeleteImageModal(image.id)}
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
              Delete Image
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default SessionDetailPage;
