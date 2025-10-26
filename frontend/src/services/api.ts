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
  MergeStudentData,
  MergeStudentResponse,
  Session,
  CreateSessionData,
  UpdateSessionData,
  Image,
  FaceCrop,
  FaceCropDetail,
  UpdateFaceCropData,
  ProcessImageData,
  ProcessImageResponse,
  StudentDetailReport,
  AttendanceReport,
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

  getAttendanceReport: async (
    id: number,
    params?: {
      include_unprocessed?: boolean;
      date_from?: string;
      date_to?: string;
    }
  ): Promise<AttendanceReport> => {
    const response = await api.get<AttendanceReport>(`/attendance/classes/${id}/attendance-report/`, {
      params,
    });
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

  getSessionFaceCrops: async (
    sessionId: number,
    params?: {
      is_identified?: boolean;
      student_id?: number;
      sort_by?: string;
    }
  ): Promise<{
    session_id: number;
    session_name: string;
    total_crops: number;
    identified_crops: number;
    unidentified_crops: number;
    face_crops: FaceCropDetail[];
  }> => {
    const response = await api.get(`/attendance/sessions/${sessionId}/face-crops/`, { params });
    return response.data;
  },
};

// Students API
export const studentsAPI = {
  getStudents: async (classId?: number, pageSize: number = 10000): Promise<Student[]> => {
    const params = classId ? { class_id: classId, page_size: pageSize } : { page_size: pageSize };
    const response = await api.get<PaginatedResponse<Student>>('/attendance/students/', { params });
    return response.data.results;
  },

  getStudent: async (id: number): Promise<Student> => {
    const response = await api.get<Student>(`/attendance/students/${id}/`);
    return response.data;
  },

  getStudentDetailReport: async (id: number): Promise<StudentDetailReport> => {
    const response = await api.get<StudentDetailReport>(`/attendance/students/${id}/detail-report/`);
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

  mergeStudents: async (sourceStudentId: number, data: MergeStudentData): Promise<MergeStudentResponse> => {
    const response = await api.post<MergeStudentResponse>(
      `/attendance/students/${sourceStudentId}/merge/`,
      data
    );
    return response.data;
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

  getImage: async (id: number): Promise<Image> => {
    const response = await api.get<Image>(`/attendance/images/${id}/`);
    return response.data;
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

  processImage: async (imageId: number, options?: ProcessImageData): Promise<ProcessImageResponse> => {
    const response = await api.post<ProcessImageResponse>(
      `/attendance/images/${imageId}/process-image/`,
      options || {}
    );
    return response.data;
  },
};

// Face Crops API
export const faceCropsAPI = {
  getFaceCrops: async (imageId: number): Promise<FaceCropDetail[]> => {
    const response = await api.get<FaceCropDetail[]>(`/attendance/images/${imageId}/face_crops/`);
    return response.data;
  },

  getFaceCrop: async (id: number): Promise<FaceCropDetail> => {
    const response = await api.get<FaceCropDetail>(`/attendance/face-crops/${id}/`);
    return response.data;
  },

  updateFaceCrop: async (id: number, data: UpdateFaceCropData): Promise<FaceCrop> => {
    const response = await api.patch<FaceCrop>(`/attendance/face-crops/${id}/`, data);
    return response.data;
  },

  unidentifyFaceCrop: async (id: number): Promise<FaceCrop> => {
    const response = await api.post<FaceCrop>(`/attendance/face-crops/${id}/unidentify/`);
    return response.data;
  },

  deleteFaceCrop: async (id: number): Promise<void> => {
    await api.delete(`/attendance/face-crops/${id}/`);
  },

  generateEmbedding: async (
    id: number,
    modelName: 'arcface' | 'facenet512' = 'arcface'
  ): Promise<{
    status: string;
    message: string;
    face_crop_id: number;
    model_name: string;
    embedding_dimension: number;
    embedding_preview: number[];
    has_embedding: boolean;
  }> => {
    const response = await api.post(`/attendance/face-crops/${id}/generate-embedding/`, {
      model_name: modelName,
    });
    return response.data;
  },

  assignCrop: async (
    id: number,
    options?: {
      k?: number;
      similarity_threshold?: number;
      embedding_model?: 'arcface' | 'facenet512';
      use_voting?: boolean;
      auto_commit?: boolean;
    }
  ): Promise<{
    status: string;
    crop_id: number;
    assigned: boolean;
    student_id?: number;
    student_name?: string;
    confidence?: number;
    message: string;
  }> => {
    const response = await api.post(`/attendance/face-crops/${id}/assign/`, options || {});
    return response.data;
  },
};

export default api;
