import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { 
  User, 
  LoginCredentials, 
  LoginResponse, 
  Class, 
  CreateClassData, 
  UpdateClassData,
  PaginatedResponse,
  Student,
  CreateStudentData,
  UpdateStudentData,
  Session,
  CreateSessionData,
  UpdateSessionData,
  Image,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export const tokenManager = {
  getAccessToken: (): string | null => localStorage.getItem(TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (access: string, refresh: string): void => {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  clearTokens: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = tokenManager.getRefreshToken();
        if (refreshToken) {
          const response = await axios.post<{ access: string }>(
            `${API_BASE_URL}/auth/jwt/refresh/`,
            { refresh: refreshToken }
          );
          
          const newAccessToken = response.data.access;
          tokenManager.setTokens(newAccessToken, refreshToken);
          
          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          }
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        tokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/jwt/create/', credentials);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/users/me/');
    return response.data;
  },

  logout: async (): Promise<void> => {
    tokenManager.clearTokens();
  },

  verifyToken: async (): Promise<boolean> => {
    try {
      const token = tokenManager.getAccessToken();
      if (!token) return false;
      
      await api.post('/auth/jwt/verify/', { token });
      return true;
    } catch {
      return false;
    }
  },
};

// Classes API
export const classesAPI = {
  getClasses: async (): Promise<Class[]> => {
    const response = await api.get<PaginatedResponse<Class>>('/attendance/classes/');
    return response.data.results;
  },

  getClass: async (id: number): Promise<Class> => {
    const response = await api.get<Class>(`/attendance/classes/${id}/`);
    return response.data;
  },

  createClass: async (data: CreateClassData): Promise<Class> => {
    const response = await api.post<Class>('/attendance/classes/', data);
    return response.data;
  },

  updateClass: async (id: number, data: UpdateClassData): Promise<Class> => {
    const response = await api.patch<Class>(`/attendance/classes/${id}/`, data);
    return response.data;
  },

  deleteClass: async (id: number): Promise<void> => {
    await api.delete(`/attendance/classes/${id}/`);
  },

  getClassStatistics: async (id: number): Promise<{
    student_count: number;
    session_count: number;
    total_images: number;
    processed_images: number;
    total_face_crops: number;
    identified_faces: number;
  }> => {
    const response = await api.get(`/attendance/classes/${id}/statistics/`);
    return response.data;
  },
};

// Sessions API
export const sessionsAPI = {
  getSessions: async (classId?: number): Promise<Session[]> => {
    const params = classId ? { class_id: classId } : {};
    const response = await api.get<PaginatedResponse<Session>>('/attendance/sessions/', { params });
    return response.data.results;
  },

  getSession: async (id: number): Promise<Session> => {
    const response = await api.get<Session>(`/attendance/sessions/${id}/`);
    return response.data;
  },

  createSession: async (data: CreateSessionData): Promise<Session> => {
    const response = await api.post<Session>('/attendance/sessions/', data);
    return response.data;
  },

  updateSession: async (id: number, data: UpdateSessionData): Promise<Session> => {
    const response = await api.patch<Session>(`/attendance/sessions/${id}/`, data);
    return response.data;
  },

  deleteSession: async (id: number): Promise<void> => {
    await api.delete(`/attendance/sessions/${id}/`);
  },
};

// Students API
export const studentsAPI = {
  getStudents: async (classId?: number): Promise<Student[]> => {
    const params = classId ? { class_id: classId, page_size: 1000 } : { page_size: 1000 };
    const response = await api.get<PaginatedResponse<Student>>('/attendance/students/', { params });
    return response.data.results;
  },

  getStudent: async (id: number): Promise<Student> => {
    const response = await api.get<Student>(`/attendance/students/${id}/`);
    return response.data;
  },

  createStudent: async (data: CreateStudentData): Promise<Student> => {
    const response = await api.post<Student>('/attendance/students/', data);
    return response.data;
  },

  updateStudent: async (id: number, data: UpdateStudentData): Promise<Student> => {
    const response = await api.patch<Student>(`/attendance/students/${id}/`, data);
    return response.data;
  },

  deleteStudent: async (id: number): Promise<void> => {
    await api.delete(`/attendance/students/${id}/`);
  },

  bulkUploadStudents: async (classId: number, file: File, hasHeader: boolean): Promise<{
    created: Student[];
    total_created: number;
    total_skipped: number;
    skipped: Array<{ first_name: string; last_name: string; student_id: string; reason: string }>;
    message: string;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('has_header', hasHeader.toString());

    const response = await api.post(
      `/attendance/classes/${classId}/bulk-upload-students/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};

// Images API
export const imagesAPI = {
  getImages: async (sessionId: number): Promise<Image[]> => {
    const response = await api.get<PaginatedResponse<Image>>('/attendance/images/', {
      params: { session_id: sessionId, page_size: 1000 }
    });
    return response.data.results;
  },

  uploadImage: async (sessionId: number, file: File): Promise<Image> => {
    const formData = new FormData();
    formData.append('session', sessionId.toString());
    formData.append('original_image_path', file);

    const response = await api.post<Image>('/attendance/images/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteImage: async (id: number): Promise<void> => {
    await api.delete(`/attendance/images/${id}/`);
  },
};

export default api;
