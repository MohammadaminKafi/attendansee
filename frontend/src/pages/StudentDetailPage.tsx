import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { studentsAPI, classesAPI } from '@/services/api';
import { StudentDetailReport, Class } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ArrowLeft, CheckCircle, XCircle, User, Calendar, TrendingUp, Image as ImageIcon, Upload, Trash2, Check } from 'lucide-react';

const StudentDetailPage: React.FC = () => {
  const { classId, studentId } = useParams<{ classId: string; studentId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [report, setReport] = useState<StudentDetailReport | null>(null);
  const [classData, setClassData] = useState<Class | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const [settingFromCrop, setSettingFromCrop] = useState(false);
  const [hoveredCropId, setHoveredCropId] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, [classId, studentId]);

  const loadData = async () => {
    if (!classId || !studentId) return;

    try {
      setLoading(true);
      setError(null);

      const [reportData, classInfo] = await Promise.all([
        studentsAPI.getStudentDetailReport(parseInt(studentId)),
        classesAPI.getClass(parseInt(classId)),
      ]);

      setReport(reportData);
      setClassData(classInfo);
    } catch (err: any) {
      console.error('Error loading student report:', err);
      setError(err.response?.data?.detail || 'Failed to load student data');
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (path: string) => {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const baseUrl = API_BASE.replace('/api', '');
    return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatTime = (timeString: string | null) => {
    if (!timeString) return 'N/A';
    return timeString;
  };

  const handleProfilePictureUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !studentId) return;

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size too large. Maximum size is 5MB.');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Invalid file type. Please upload an image file.');
      return;
    }

    try {
      setUploadingPicture(true);
      setError(null);
      const response = await studentsAPI.uploadProfilePicture(parseInt(studentId), file);
      
      // Update the student data in the report
      if (report) {
        setReport({
          ...report,
          student: response.student,
        });
      }
    } catch (err: any) {
      console.error('Error uploading profile picture:', err);
      setError(err.response?.data?.error || 'Failed to upload profile picture');
    } finally {
      setUploadingPicture(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteProfilePicture = async () => {
    if (!studentId || !report?.student.profile_picture) return;

    try {
      setUploadingPicture(true);
      setError(null);
      const response = await studentsAPI.deleteProfilePicture(parseInt(studentId));
      
      // Update the student data in the report
      if (report) {
        setReport({
          ...report,
          student: response.student,
        });
      }
    } catch (err: any) {
      console.error('Error deleting profile picture:', err);
      setError(err.response?.data?.error || 'Failed to delete profile picture');
    } finally {
      setUploadingPicture(false);
    }
  };

  const handleSetProfileFromCrop = async (faceCropId: number) => {
    if (!studentId) return;

    try {
      setSettingFromCrop(true);
      setError(null);
      const response = await studentsAPI.setProfilePictureFromCrop(parseInt(studentId), faceCropId);
      
      // Update the student data in the report
      if (report) {
        setReport({
          ...report,
          student: response.student,
        });
      }
    } catch (err: any) {
      console.error('Error setting profile from crop:', err);
      setError(err.response?.data?.error || 'Failed to set profile picture from face crop');
    } finally {
      setSettingFromCrop(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !report || !classData) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-danger mb-4">Error</h2>
          <p className="text-gray-300 mb-4">{error || 'Student not found'}</p>
          <button
            onClick={() => navigate(`/classes/${classId}`)}
            className="text-primary hover:text-primary-light transition-colors"
          >
            ← Back to Class
          </button>
        </div>
      </div>
    );
  }

  const { student, statistics, sessions } = report;

  const breadcrumbItems = [
    { label: 'Classes', path: '/classes' },
    { label: classData.name, path: `/classes/${classId}` },
    { label: student.full_name },
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

      {/* Student Header */}
      <Card className="mb-6">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-start gap-4">
            {/* Profile Picture */}
            <div className="relative group">
              <div className="w-20 h-20 rounded-full overflow-hidden bg-dark-hover flex items-center justify-center border-2 border-dark-border">
                {student.profile_picture ? (
                  <img
                    src={student.profile_picture}
                    alt={student.full_name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-10 h-10 text-gray-400" />
                )}
              </div>
              
              {/* Upload/Delete buttons overlay */}
              <div className="absolute inset-0 bg-black bg-opacity-60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleProfilePictureUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingPicture}
                  className="p-2 bg-primary hover:bg-primary-light rounded-full text-white transition-colors disabled:opacity-50"
                  title="Upload profile picture"
                >
                  <Upload className="w-4 h-4" />
                </button>
                {student.profile_picture && (
                  <button
                    onClick={handleDeleteProfilePicture}
                    disabled={uploadingPicture}
                    className="p-2 bg-danger hover:bg-danger/80 rounded-full text-white transition-colors disabled:opacity-50"
                    title="Delete profile picture"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{student.full_name}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                {student.student_id && <span>ID: {student.student_id}</span>}
                {student.email && <span>Email: {student.email}</span>}
              </div>
              <div className="mt-2">
                <Badge variant="info">
                  {classData.name}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-center gap-3 mb-2">
              <Calendar className="w-5 h-5 text-primary" />
              <p className="text-sm text-gray-400">Total Sessions</p>
            </div>
            <p className="text-2xl font-bold text-white">{statistics.total_sessions}</p>
          </div>

          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle className="w-5 h-5 text-success" />
              <p className="text-sm text-gray-400">Attended</p>
            </div>
            <p className="text-2xl font-bold text-white">{statistics.attended_sessions}</p>
          </div>

          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-center gap-3 mb-2">
              <XCircle className="w-5 h-5 text-danger" />
              <p className="text-sm text-gray-400">Missed</p>
            </div>
            <p className="text-2xl font-bold text-white">{statistics.missed_sessions}</p>
          </div>

          <div className="p-4 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-warning" />
              <p className="text-sm text-gray-400">Attendance Rate</p>
            </div>
            <p className="text-2xl font-bold text-white">{statistics.attendance_rate}%</p>
          </div>
        </div>
      </Card>

      {/* Session Attendance List */}
      <Card>
        <h2 className="text-xl font-semibold text-white mb-4">Session Attendance</h2>
        
        {sessions.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p>No sessions available</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className="border border-dark-border rounded-lg overflow-hidden hover:border-primary/50 transition-colors"
              >
                {/* Session Header */}
                <div className="p-4 bg-dark-hover flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">{session.session_name}</h3>
                      {session.was_present ? (
                        <Badge variant="success">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Present
                        </Badge>
                      ) : (
                        <Badge variant="danger">
                          <XCircle className="w-3 h-3 mr-1" />
                          Absent
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span>{formatDate(session.date)}</span>
                      {session.start_time && (
                        <span>
                          {formatTime(session.start_time)} - {formatTime(session.end_time)}
                        </span>
                      )}
                      {session.detection_count > 0 && (
                        <span className="text-primary">
                          {session.detection_count} detection{session.detection_count !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => navigate(`/classes/${classId}/sessions/${session.session_id}`)}
                  >
                    View Session
                  </Button>
                </div>

                {/* Face Crops */}
                {session.face_crops.length > 0 && (
                  <div className="p-4 bg-dark-card">
                    <div className="flex items-center gap-2 mb-3">
                      <ImageIcon className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-400">
                        Face Detections ({session.face_crops.length})
                      </span>
                    </div>
                    <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
                      {session.face_crops.map((crop) => (
                        <div
                          key={crop.id}
                          className="relative group aspect-square rounded-lg overflow-hidden border border-dark-border hover:border-primary transition-colors"
                          onMouseEnter={() => setHoveredCropId(crop.id)}
                          onMouseLeave={() => setHoveredCropId(null)}
                        >
                          <img
                            src={getImageUrl(crop.crop_image_path)}
                            alt={`Face crop ${crop.id}`}
                            className="w-full h-full object-cover cursor-pointer"
                            onClick={() =>
                              navigate(`/classes/${classId}/sessions/${session.session_id}/images/${crop.image_id}`)
                            }
                            title={`View in Image ${crop.image_id}`}
                          />
                          
                          {/* Set as Profile button overlay */}
                          {hoveredCropId === crop.id && (
                            <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSetProfileFromCrop(crop.id);
                                }}
                                disabled={settingFromCrop}
                                className="px-2 py-1 bg-primary hover:bg-primary-light rounded text-white text-xs font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
                                title="Set as profile picture"
                              >
                                <Check className="w-3 h-3" />
                                Set as Profile
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default StudentDetailPage;
