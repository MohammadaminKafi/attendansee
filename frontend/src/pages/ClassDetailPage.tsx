import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { classesAPI } from '@/services/api';
import { Class } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { Tabs, Tab } from '@/components/ui/Tabs';
import { StatCard } from '@/components/ui/StatCard';
import { SessionsTab } from '@/components/tabs/SessionsTab';
import { StudentsTab } from '@/components/tabs/StudentsTab';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';

export const ClassDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [classData, setClassData] = useState<Class | null>(null);
  const [statistics, setStatistics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('sessions');

  const tabs: Tab[] = [
    { id: 'sessions', label: 'Sessions', icon: '📅' },
    { id: 'students', label: 'Students', icon: '👥' },
  ];

  useEffect(() => {
    if (id) {
      loadClassData();
    } else {
      setError('Invalid class ID');
      setLoading(false);
    }
  }, [id]);

  const loadClassData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError('');
      const [classResponse, statsResponse] = await Promise.all([
        classesAPI.getClass(parseInt(id)),
        classesAPI.getClassStatistics(parseInt(id)),
      ]);
      setClassData(classResponse);
      setStatistics(statsResponse);
    } catch (err: any) {
      console.error('Failed to load class data:', err);
      setError(err.response?.data?.detail || 'Failed to load class data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !classData) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-red-400 mb-4">Error</h2>
          <p className="text-slate-300 mb-4">{error || 'Class not found'}</p>
          <button
            onClick={() => navigate('/classes')}
            className="text-blue-400 hover:text-blue-300"
          >
            ← Back to Classes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate('/classes')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Classes
        </Button>

        {/* Breadcrumb */}
        <Breadcrumb
          items={[
            { label: 'Classes', href: '/classes' },
            { label: classData.name },
          ]}
          className="mb-6"
        />

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">{classData.name}</h1>
          {classData.description && (
            <p className="text-slate-400">{classData.description}</p>
          )}
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Students"
              value={statistics.student_count}
              icon="👥"
              iconColor="text-blue-500"
            />
            <StatCard
              label="Total Sessions"
              value={statistics.session_count}
              icon="📅"
              iconColor="text-green-500"
            />
            <StatCard
              label="Total Images"
              value={statistics.total_images}
              icon="📸"
              iconColor="text-purple-500"
            />
            <StatCard
              label="Identified Faces"
              value={`${statistics.identified_faces} / ${statistics.total_face_crops}`}
              icon="🔍"
              iconColor="text-yellow-500"
            />
          </div>
        )}

        {/* Tabs */}
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} className="mb-6" />

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'sessions' && id && (
            <SessionsTab classId={parseInt(id)} onUpdate={loadClassData} />
          )}
          {activeTab === 'students' && id && (
            <StudentsTab classId={parseInt(id)} onUpdate={loadClassData} />
          )}
        </div>
      </div>
    </div>
  );
};
