import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { studentsAPI, classesAPI, faceCropsAPI } from '@/services/api';
import { StudentDetailReport, Class } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ActionsMenu } from '@/components/ui/ActionsMenu';
import { ConfirmationModal } from '@/components/ui/ConfirmationModal';
import { Modal } from '@/components/ui/Modal';
import { ArrowLeft, CheckCircle, XCircle, User, Calendar, TrendingUp, Image as ImageIcon, Upload, Trash2, Check, Hand, RotateCcw, Edit2, UserX } from 'lucide-react';

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
  const [togglingAttendance, setTogglingAttendance] = useState<number | null>(null);
  const [showUnassignAllModal, setShowUnassignAllModal] = useState(false);
  const [managementProcessing, setManagementProcessing] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState({ first_name: '', last_name: '', student_id: '', email: '' });
  const [loadingManualAttendance] = useState(false);
  const [showManualAttendanceModal, setShowManualAttendanceModal] = useState(false);

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
const handleToggleManualAttendance = async (sessionId: number, currentIsManual: boolean, currentWasPresent: boolean) => {
    if (!studentId) return;
    
    try {
      setTogglingAttendance(sessionId);
      setError(null);
      
      // Cycle through 3 states: Auto -> Present -> Absent -> Auto
      if (!currentIsManual) {
        // Currently Auto -> Mark as Present
        await studentsAPI.markSessionAttendance(parseInt(studentId), {
          session_id: sessionId,
          is_present: true,
        });
      } else if (currentWasPresent) {
        // Currently Present -> Mark as Absent
        await studentsAPI.markSessionAttendance(parseInt(studentId), {
          session_id: sessionId,
          is_present: false,
        });
      } else {
        // Currently Absent -> Clear to Auto
        await studentsAPI.unmarkAttendance(parseInt(studentId), sessionId);
      }
      
      // Refresh sessions to show updated state
      await loadData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle attendance';
      setError(errorMessage);
    } finally {
      setTogglingAttendance(null);
    }
  };

  const handleUnassignAllFaces = async () => {
    if (!studentId) return;

    try {
      setManagementProcessing(true);
      await studentsAPI.unassignAllFaces(parseInt(studentId));
      
      // Reload data
      await loadData();
      setShowUnassignAllModal(false);
    } catch (err: any) {
      console.error('Error unassigning all faces:', err);
      setError(err.response?.data?.error || 'Failed to unassign all faces');
    } finally {
      setManagementProcessing(false);
    }
  };

  const handleOpenEditModal = () => {
    if (!report) return;
    setEditFormData({
      first_name: report.student.first_name,
      last_name: report.student.last_name,
      student_id: report.student.student_id || '',
      email: report.student.email || '',
    });
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!studentId) return;

    try {
      const updatedStudent = await studentsAPI.updateStudent(parseInt(studentId), editFormData);
      
      // Update the student data in the report
      if (report) {
        setReport({
          ...report,
          student: updatedStudent,
        });
      }
      setShowEditModal(false);
    } catch (err: any) {
      console.error('Error updating student:', err);
      setError(err.response?.data?.error || 'Failed to update student information');
    }
  };

  const handleUnassignFaceCrop = async (cropId: number) => {
    try {
      await faceCropsAPI.unidentifyFaceCrop(cropId);
      
      // Reload data to refresh face crops
      await loadData();
    } catch (err: any) {
      console.error('Error unassigning face crop:', err);
      setError(err.response?.data?.error || 'Failed to unassign face crop');
    }
  };

  const handleMarkManualAttendance = () => {
    setShowManualAttendanceModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!report || !classData) {
    return (
      <div className="p-8">
        <p className="text-danger">{error || 'Student not found'}</p>
      </div>
    );
  }

  const { student, statistics, sessions } = report;

  const breadcrumbItems = [
    { label: 'Classes', href: '/classes' },
    { label: classData.name, href: `/classes/${classId}` },
    { label: 'Students', href: `/classes/${classId}` },
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
          <Button onClick={handleOpenEditModal} variant="secondary">
            <Edit2 className="w-4 h-4 mr-2" />
            Edit Info
          </Button>
        </div>

        {/* Actions Menu */}
        <div className="mb-6">
          <ActionsMenu
            categories={[
              {
                label: 'Manual Actions',
                items: [
                  {
                    id: 'manual-attendance',
                    label: 'Mark Manual Attendance',
                    description: 'Manually mark student attendance across sessions',
                    icon: <Hand className="w-5 h-5" />,
                    onClick: handleMarkManualAttendance,
                    disabled: loadingManualAttendance,
                    isProcessing: loadingManualAttendance,
                  },
                ],
              },
              {
                label: 'Management',
                items: [
                  {
                    id: 'unassign-all',
                    label: 'Unassign All Faces',
                    description: `Remove all face crop assignments from this student. ${statistics.total_detections} face crop(s) assigned.`,
                    icon: <RotateCcw className="w-5 h-5" />,
                    onClick: () => setShowUnassignAllModal(true),
                    disabled: managementProcessing || statistics.total_detections === 0,
                    isProcessing: false,
                  },
                ],
              },
            ]}
          />
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
                          {session.is_manual && <Hand className="w-3 h-3 mr-1" />}
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Present
                        </Badge>
                      ) : (
                        <Badge variant="danger">
                          {session.is_manual && <Hand className="w-3 h-3 mr-1" />}
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
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 border border-dark-border rounded-lg p-1">
                      <button
                        onClick={() => handleToggleManualAttendance(session.session_id, session.is_manual, session.was_present)}
                        disabled={togglingAttendance === session.session_id}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          session.is_manual && session.was_present
                            ? 'bg-success text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Mark as Present"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleToggleManualAttendance(session.session_id, session.is_manual, session.was_present)}
                        disabled={togglingAttendance === session.session_id}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          session.is_manual && !session.was_present
                            ? 'bg-danger text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Mark as Absent"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleToggleManualAttendance(session.session_id, session.is_manual, session.was_present)}
                        disabled={togglingAttendance === session.session_id}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          !session.is_manual
                            ? 'bg-primary text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Auto (based on face detection)"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => navigate(`/classes/${classId}/sessions/${session.session_id}`)}
                    >
                      View Session
                    </Button>
                  </div>
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
                            <div className="absolute inset-0 bg-black bg-opacity-60 flex flex-col items-center justify-center gap-1">
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
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleUnassignFaceCrop(crop.id);
                                }}
                                className="px-2 py-1 bg-danger/80 hover:bg-danger rounded text-white text-xs font-medium transition-colors flex items-center gap-1"
                                title="Unassign this face crop"
                              >
                                <UserX className="w-3 h-3" />
                                Unassign
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

      {/* Edit Student Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Student Information"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              First Name
            </label>
            <input
              type="text"
              value={editFormData.first_name}
              onChange={(e) => setEditFormData({ ...editFormData, first_name: e.target.value })}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Last Name
            </label>
            <input
              type="text"
              value={editFormData.last_name}
              onChange={(e) => setEditFormData({ ...editFormData, last_name: e.target.value })}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Student ID
            </label>
            <input
              type="text"
              value={editFormData.student_id}
              onChange={(e) => setEditFormData({ ...editFormData, student_id: e.target.value })}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={editFormData.email}
              onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowEditModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveEdit}
              className="flex-1"
            >
              Save Changes
            </Button>
          </div>
        </div>
      </Modal>

      {/* Unassign All Confirmation Modal */}
      <ConfirmationModal
        isOpen={showUnassignAllModal}
        onClose={() => setShowUnassignAllModal(false)}
        onConfirm={handleUnassignAllFaces}
        title="Unassign All Faces"
        message={`Are you sure you want to unassign all ${statistics.total_detections} face crop(s) from ${student.full_name}? This will remove all assignments but keep the face crops.`}
        confirmText="Unassign All"
        isDestructive={false}
        isProcessing={managementProcessing}
      />

      {/* Manual Attendance Modal */}
      <Modal
        isOpen={showManualAttendanceModal}
        onClose={() => setShowManualAttendanceModal(false)}
        title={`Manual Attendance - ${student.full_name}`}
      >
        <div className="space-y-4">
          {sessions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400">No sessions available</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {sessions.map((session) => {
                const isMarkedPresent = session.is_manual && session.was_present;
                const isMarkedAbsent = session.is_manual && !session.was_present;
                const isAuto = !session.is_manual;
                
                return (
                  <div
                    key={session.session_id}
                    className="flex items-center justify-between p-3 bg-dark-hover rounded-lg hover:bg-dark-border transition-colors"
                  >
                    <div className="flex-1">
                      <p className="text-white font-medium">{session.session_name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(session.date).toLocaleDateString()} 
                        {session.start_time && ` • ${session.start_time}`}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-1 border border-dark-border rounded-lg p-1">
                      <button
                        onClick={() => handleToggleManualAttendance(session.session_id, session.is_manual, session.was_present)}
                        disabled={togglingAttendance === session.session_id}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          isMarkedPresent
                            ? 'bg-success text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Mark as Present"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleToggleManualAttendance(session.session_id, session.is_manual, session.was_present)}
                        disabled={togglingAttendance === session.session_id}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          isMarkedAbsent
                            ? 'bg-danger text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Mark as Absent"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleToggleManualAttendance(session.session_id, session.is_manual, session.was_present)}
                        disabled={togglingAttendance === session.session_id || isAuto}
                        className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                          isAuto
                            ? 'bg-primary text-white'
                            : 'hover:bg-dark-hover text-gray-400'
                        }`}
                        title="Auto (based on face detection)"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-dark-border">
            <Button
              variant="secondary"
              onClick={() => setShowManualAttendanceModal(false)}
            >
              Done
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default StudentDetailPage;
