// User types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

// Class types
export interface Class {
  id: number;
  owner: string;
  owner_id: number;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  student_count: number;
  session_count: number;
}

export interface CreateClassData {
  name: string;
  description?: string;
  is_active?: boolean;
}

export interface UpdateClassData {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// Student types
export interface Student {
  id: number;
  class_enrolled: number;
  class_name: string;
  first_name: string;
  last_name: string;
  full_name: string;
  student_id: string;
  email: string;
  created_at: string;
}

export interface CreateStudentData {
  class_enrolled: number;
  first_name: string;
  last_name: string;
  student_id?: string;
  email?: string;
}

export interface UpdateStudentData {
  first_name?: string;
  last_name?: string;
  student_id?: string;
  email?: string;
}

// Session types
export interface Session {
  id: number;
  class_session: number;
  class_name: string;
  name: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  notes: string;
  is_processed: boolean;
  created_at: string;
  updated_at: string;
  image_count: number;
  identified_faces_count: number;
  total_faces_count: number;
}

export interface CreateSessionData {
  class_session: number;
  name: string;
  date?: string;
  start_time?: string;
  end_time?: string;
  notes?: string;
}

export interface UpdateSessionData {
  name?: string;
  date?: string;
  start_time?: string | null;
  end_time?: string | null;
  notes?: string;
}

// Image types
export interface Image {
  id: number;
  session: number;
  session_name: string;
  class_name: string;
  original_image_path: string;
  processed_image_path: string | null;
  upload_date: string;
  is_processed: boolean;
  processing_date: string | null;
  created_at: string;
  updated_at: string;
  face_crop_count: number;
}

export interface CreateImageData {
  session: number;
  original_image_path: File;
}

// Statistics types
export interface ClassStatistics {
  student_count: number;
  session_count: number;
  total_images: number;
  processed_images: number;
  total_face_crops: number;
  identified_faces: number;
}

// API Response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Error types
export interface APIError {
  detail?: string;
  [key: string]: string | string[] | undefined;
}
