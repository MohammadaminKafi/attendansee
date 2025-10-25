import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';
import { LoginPage } from '@/pages/LoginPage';
import { ClassesPage } from '@/pages/ClassesPage';
import { ClassDetailPage } from '@/pages/ClassDetailPage';
import SessionDetailPage from '@/pages/SessionDetailPage';
import ImageDetailPage from '@/pages/ImageDetailPage';
import StudentDetailPage from '@/pages/StudentDetailPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/classes" element={<ClassesPage />} />
            <Route path="/classes/:id" element={<ClassDetailPage />} />
            <Route path="/classes/:classId/students/:studentId" element={<StudentDetailPage />} />
            <Route path="/classes/:classId/sessions/:sessionId" element={<SessionDetailPage />} />
            <Route path="/classes/:classId/sessions/:sessionId/images/:imageId" element={<ImageDetailPage />} />
            <Route path="/" element={<Navigate to="/classes" replace />} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

