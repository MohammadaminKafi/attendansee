import React, { useState, useEffect } from 'react';
import { classesAPI } from '@/services/api';
import { AttendanceReport } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle, XCircle, Download } from 'lucide-react';

interface ReportTabProps {
  classId: number;
}

export const ReportTab: React.FC<ReportTabProps> = ({ classId }) => {
  const [report, setReport] = useState<AttendanceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReport();
  }, [classId]);

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

  const exportToCSV = () => {
    if (!report) return;

    // Prepare CSV header
    const headers = ['Student Name', 'Student ID', 'Email', 'Attendance Rate'];
    report.sessions.forEach((session) => {
      headers.push(`${session.name} (${new Date(session.date).toLocaleDateString()})`);
    });

    // Prepare CSV rows
    const rows = report.attendance_matrix.map((student) => {
      const row = [
        student.full_name,
        student.student_number,
        student.email || '',
        `${student.attendance_rate}%`,
      ];

      // Add attendance for each session
      student.session_attendance.forEach((attendance) => {
        row.push(attendance.present ? 'Present' : 'Absent');
      });

      return row;
    });

    // Generate CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    // Download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${report.class_name}_attendance_report.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
        <button
          onClick={exportToCSV}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark rounded-lg text-white transition-colors"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
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
                {student.session_attendance.map((attendance, sessionIndex) => (
                  <td
                    key={sessionIndex}
                    className="px-3 py-3 text-center border-r border-dark-border"
                  >
                    {attendance.present ? (
                      <div className="flex flex-col items-center gap-1">
                        <CheckCircle className="w-5 h-5 text-success" />
                        {attendance.detection_count > 1 && (
                          <span className="text-xs text-gray-500">
                            {attendance.detection_count}×
                          </span>
                        )}
                      </div>
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-600 mx-auto" />
                    )}
                  </td>
                ))}
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
          <Badge variant="success">80%+</Badge>
          <Badge variant="warning">60-79%</Badge>
          <Badge variant="danger">&lt;60%</Badge>
        </div>
      </div>
    </div>
  );
};
