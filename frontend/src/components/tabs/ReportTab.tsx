import React, { useState, useEffect, useRef } from 'react';
import { classesAPI, sessionsAPI } from '@/services/api';
import { AttendanceReport } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle, XCircle, Download, FileText, ChevronDown, Hand, RotateCcw } from 'lucide-react';

interface ReportTabProps {
  classId: number;
}

export const ReportTab: React.FC<ReportTabProps> = ({ classId }) => {
  const [report, setReport] = useState<AttendanceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [hoveredCell, setHoveredCell] = useState<{ studentId: number; sessionId: number } | null>(null);
  const [togglingCell, setTogglingCell] = useState<{ studentId: number; sessionId: number } | null>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadReport();
  }, [classId]);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await classesAPI.getAttendanceReport(classId);
      setReport(data);
    } catch (err: any) {
      console.error('Failed to load attendance report:', err);
      setError(err.response?.data?.detail || 'Failed to load attendance report');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAttendance = async (sessionId: number, studentId: number, isPresent: boolean) => {
    try {
      setTogglingCell({ studentId, sessionId });
      await sessionsAPI.markAttendance(sessionId, {
        student_id: studentId,
        is_present: isPresent,
      });
      await loadReport();
    } catch (err) {
      console.error('Error marking attendance:', err);
    } finally {
      setTogglingCell(null);
    }
  };

  const handleUnmarkAttendance = async (sessionId: number, studentId: number) => {
    try {
      setTogglingCell({ studentId, sessionId });
      await sessionsAPI.unmarkAttendance(sessionId, studentId);
      await loadReport();
    } catch (err) {
      console.error('Error unmarking attendance:', err);
    } finally {
      setTogglingCell(null);
    }
  };

  const exportToCSV = () => {
    if (!report) return;

    setShowExportMenu(false);

    const totalSessions = report.sessions.length;

    // Prepare CSV header
    const headers = ['Student Name', 'Student ID', 'Email', `Sessions Present (/${totalSessions})`, 'Attendance Rate'];
    report.sessions.forEach((session) => {
      headers.push(`${session.name} (${new Date(session.date).toLocaleDateString()})`);
    });

    // Prepare CSV rows
    const rows = report.attendance_matrix.map((student) => {
      // Count present sessions
      const presentCount = student.session_attendance.filter(a => a.present).length;
      
      const row = [
        student.full_name,
        student.student_number,
        student.email || '',
        `${presentCount}`,
        `${student.attendance_rate}%`,
      ];

      // Add attendance for each session
      student.session_attendance.forEach((attendance) => {
        row.push(attendance.present ? '1' : '0');
      });

      return row;
    });

    // Generate CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    // Add UTF-8 BOM (Byte Order Mark) to ensure proper encoding of non-ASCII characters
    const BOM = '\uFEFF';
    const csvWithBOM = BOM + csvContent;

    // Download CSV file
    const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${report.class_name}_attendance_report.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToPDF = async () => {
    if (!report) return;

    setShowExportMenu(false);
    setExportingPDF(true);
    
    try {
      const blob = await classesAPI.exportAttendancePDF(classId);
      
      // Verify we got a valid blob with PDF content
      if (!blob || !(blob instanceof Blob) || blob.size === 0) {
        throw new Error('Invalid response from server');
      }
      
      // Verify it's actually a PDF
      if (blob.type && !blob.type.includes('pdf') && !blob.type.includes('application/octet-stream')) {
        throw new Error(`Unexpected content type: ${blob.type}`);
      }
      
      // Download PDF file
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `${report.class_name.replace(/ /g, '_')}_attendance_report.pdf`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 100);
      
      // Reset state immediately after triggering download
      setExportingPDF(false);
    } catch (error: any) {
      console.error('Failed to export PDF:', error);
      console.error('Error details:', error?.response?.data, error?.message);
      alert('Failed to export PDF. Please try again.');
      setExportingPDF(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="text-center py-12">
        <p className="text-danger">{error || 'Failed to load report'}</p>
      </div>
    );
  }

  if (report.total_sessions === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>No sessions available to generate report</p>
      </div>
    );
  }

  if (report.total_students === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>No students enrolled in this class</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-semibold text-white mb-2">Attendance Report</h2>
          <p className="text-sm text-gray-400">
            {report.total_students} students × {report.total_sessions} sessions
          </p>
        </div>
        <div className="relative" ref={exportMenuRef}>
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            disabled={exportingPDF}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark rounded-lg text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            {exportingPDF ? 'Exporting...' : 'Export'}
            <ChevronDown className="w-4 h-4" />
          </button>
          
          {showExportMenu && !exportingPDF && (
            <div className="absolute right-0 mt-2 w-48 bg-dark-card border border-dark-border rounded-lg shadow-lg z-10">
              <button
                onClick={exportToCSV}
                className="w-full flex items-center gap-2 px-4 py-3 text-white hover:bg-dark-hover transition-colors text-left rounded-t-lg"
              >
                <Download className="w-4 h-4" />
                Export as CSV
              </button>
              <button
                onClick={exportToPDF}
                className="w-full flex items-center gap-2 px-4 py-3 text-white hover:bg-dark-hover transition-colors text-left rounded-b-lg border-t border-dark-border"
              >
                <FileText className="w-4 h-4" />
                Export as PDF
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Attendance Table */}
      <div className="overflow-x-auto border border-dark-border rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-dark-card border-b border-dark-border sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-gray-300 font-medium sticky left-0 bg-dark-card z-10 border-r border-dark-border min-w-[200px]">
                Student
              </th>
              <th className="px-4 py-3 text-center text-gray-300 font-medium border-r border-dark-border min-w-[100px]">
                Rate
              </th>
              {report.sessions.map((session) => (
                <th
                  key={session.id}
                  className="px-3 py-3 text-center text-gray-300 font-medium border-r border-dark-border min-w-[120px]"
                >
                  <div className="flex flex-col items-center gap-1">
                    <span className="truncate max-w-[100px]" title={session.name}>
                      {session.name}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(session.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {report.attendance_matrix.map((student, index) => (
              <tr
                key={student.student_id}
                className={`border-b border-dark-border hover:bg-dark-hover transition-colors ${
                  index % 2 === 0 ? 'bg-dark-bg' : 'bg-dark-card/50'
                }`}
              >
                <td className="px-4 py-3 sticky left-0 bg-inherit z-10 border-r border-dark-border">
                  <div>
                    <p className="font-medium text-white">{student.full_name}</p>
                    <p className="text-xs text-gray-500">{student.student_number}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-center border-r border-dark-border">
                  <Badge
                    variant={
                      student.attendance_rate >= 80
                        ? 'success'
                        : student.attendance_rate >= 60
                        ? 'warning'
                        : 'danger'
                    }
                  >
                    {student.attendance_rate}%
                  </Badge>
                </td>
                {student.session_attendance.map((attendance, sessionIndex) => {
                  const sessionId = report.sessions[sessionIndex].id;
                  const isHovered = hoveredCell?.studentId === student.student_id && hoveredCell?.sessionId === sessionId;
                  const isToggling = togglingCell?.studentId === student.student_id && togglingCell?.sessionId === sessionId;
                  
                  return (
                  <td
                    key={sessionIndex}
                    className="px-3 py-3 text-center border-r border-dark-border relative"
                    onMouseEnter={() => setHoveredCell({ studentId: student.student_id, sessionId })}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    {isHovered && !isToggling ? (
                      <div className="flex items-center justify-center gap-1 border border-dark-border rounded-lg p-1 bg-dark-card">
                        <button
                          onClick={() => handleMarkAttendance(sessionId, student.student_id, true)}
                          className={`p-1 rounded transition-colors ${
                            attendance.is_manual && attendance.present
                              ? 'bg-success text-white'
                              : 'hover:bg-dark-hover text-gray-400'
                          }`}
                          title="Mark as Present"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleMarkAttendance(sessionId, student.student_id, false)}
                          className={`p-1 rounded transition-colors ${
                            attendance.is_manual && !attendance.present
                              ? 'bg-danger text-white'
                              : 'hover:bg-dark-hover text-gray-400'
                          }`}
                          title="Mark as Absent"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleUnmarkAttendance(sessionId, student.student_id)}
                          disabled={!attendance.is_manual}
                          className={`p-1 rounded transition-colors disabled:opacity-50 ${
                            !attendance.is_manual
                              ? 'bg-primary text-white'
                              : 'hover:bg-dark-hover text-gray-400'
                          }`}
                          title="Auto (based on face detection)"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                    <>
                    {attendance.present ? (
                      <div className="flex flex-col items-center gap-1">
                        <div className="flex items-center justify-center gap-1">
                          <CheckCircle className="w-5 h-5 text-success" />
                          {attendance.is_manual && (
                            <div title="Manually marked">
                              <Hand className="w-3 h-3 text-warning" />
                            </div>
                          )}
                        </div>
                        {attendance.detection_count > 1 && (
                          <span className="text-xs text-gray-500">
                            {attendance.detection_count}×
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-1">
                        <XCircle className="w-5 h-5 text-gray-600 mx-auto" />
                        {attendance.is_manual && (
                          <div title="Manually marked">
                            <Hand className="w-3 h-3 text-warning" />
                          </div>
                        )}
                      </div>
                    )}
                    </>
                    )}
                  </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-dark-card border-t border-dark-border">
            <tr>
              <td className="px-4 py-3 font-medium text-gray-300 sticky left-0 bg-dark-card z-10 border-r border-dark-border">
                Session Attendance
              </td>
              <td className="px-4 py-3 text-center border-r border-dark-border">
                <span className="text-xs text-gray-500">Average</span>
              </td>
              {report.sessions.map((session) => (
                <td
                  key={session.id}
                  className="px-3 py-3 text-center border-r border-dark-border"
                >
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-sm font-medium text-white">
                      {session.present_count}/{session.total_students}
                    </span>
                    <Badge
                      variant={
                        session.attendance_rate >= 80
                          ? 'success'
                          : session.attendance_rate >= 60
                          ? 'warning'
                          : 'danger'
                      }
                      className="text-xs"
                    >
                      {session.attendance_rate}%
                    </Badge>
                  </div>
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center gap-6 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-success" />
          <span>Present</span>
        </div>
        <div className="flex items-center gap-2">
          <XCircle className="w-4 h-4 text-gray-600" />
          <span>Absent</span>
        </div>
        <div className="flex items-center gap-2">
          <Hand className="w-4 h-4 text-warning" />
          <span>Manually marked</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success">80%+</Badge>
          <Badge variant="warning">60-79%</Badge>
          <Badge variant="danger">&lt;60%</Badge>
        </div>
      </div>
    </div>
  );
};
