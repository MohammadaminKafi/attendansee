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

export interface MergeStudentData {
  target_student_id: number;
}

export interface MergeStudentResponse {
  status: string;
  message: string;
  source_student: {
    id: number;
    full_name: string;
    student_id: string;
  };
  target_student: Student;
  statistics: {
    face_crops_transferred: number;
    target_crops_before_merge: number;
    target_crops_after_merge: number;
  };
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

export interface ProcessImageData {
  detector_backend?: 'opencv' | 'ssd' | 'dlib' | 'mtcnn' | 'retinaface' | 'mediapipe' | 'yolov8' | 'yunet';
  confidence_threshold?: number;
  apply_background_effect?: boolean;
  rectangle_color?: [number, number, number];
  rectangle_thickness?: number;
}

export interface ProcessImageResponse {
  status: string;
  image_id: number;
  session_id: number;
  class_id: number;
  faces_detected: number;
  crops_created: number[];
  processed_image_url: string;
  message: string;
}

export interface BulkProcessImagesData {
  detector_backend?: 'opencv' | 'ssd' | 'dlib' | 'mtcnn' | 'retinaface' | 'mediapipe' | 'yolov8' | 'yunet';
  confidence_threshold?: number;
  apply_background_effect?: boolean;
  rectangle_color?: [number, number, number];
  rectangle_thickness?: number;
}

export interface BulkProcessImagesResponse {
  status: string;
  class_id: number;
  class_name: string;
  total_images: number;
  processed_count: number;
  failed_count: number;
  total_faces_detected: number;
  errors?: Array<{
    image_id: number;
    session_id: number;
    error: string;
  }>;
}

export interface GenerateEmbeddingsData {
  model_name?: 'arcface' | 'facenet512';
  process_unprocessed_images?: boolean;
  detector_backend?: 'opencv' | 'ssd' | 'dlib' | 'mtcnn' | 'retinaface' | 'mediapipe' | 'yolov8' | 'yunet';
  confidence_threshold?: number;
  apply_background_effect?: boolean;
}

export interface GenerateEmbeddingsResponse {
  status: string;
  session_id?: number;
  session_name?: string;
  class_id: number;
  class_name?: string;
  model_name: string;
  total_crops: number;
  crops_with_embeddings?: number;
  crops_without_embeddings?: number;
  embeddings_generated: number;
  embeddings_failed: number;
  images_processed: number;
  errors?: Array<{
    crop_id: number;
    error: string;
  }>;
  error?: string;
  unprocessed_count?: number;
  message?: string;
}

export interface ClusterCropsData {
  max_clusters?: number;
  force_clustering?: boolean;
  similarity_threshold?: number;
}

export interface ClusterCropsResponse {
  status: string;
  session_id?: number;
  session_name?: string;
  class_id?: number;
  class_name?: string;
  total_face_crops: number;
  crops_with_embeddings: number;
  crops_without_embeddings: number;
  identified_crops: number;
  unidentified_crops: number;
  clusters_created: number;
  students_created: number;
  crops_assigned: number;
  outliers: number;
  student_names: string[];
  session_breakdown?: Array<{
    session_id: number;
    session_name: string;
    crops_assigned: number;
    unique_students: number;
  }>;
  error?: string;
}

// Face Crop types
export interface FaceCrop {
  id: number;
  image: number;
  image_id: number;
  student: number | null;
  student_name: string | null;
  crop_image_path: string;
  coordinates: string;
  coordinates_dict: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null;
  confidence_score: number | null;
  is_identified: boolean;
  embedding_model: string | null;
  embedding: number[] | null;
  created_at: string;
  updated_at: string;
}

export interface FaceCropDetail extends FaceCrop {
  session_id: number;
  session_name: string;
  class_id: number;
  class_name: string;
}

export interface UpdateFaceCropData {
  student: number | null;
  confidence_score?: number;
}

// Statistics types
export interface ClassStatistics {
  student_count: number;
  session_count: number;
  total_images: number;
  processed_images: number;
  unprocessed_images_count: number;
  total_face_crops: number;
  crops_with_embeddings: number;
  crops_without_embeddings: number;
  identified_faces: number;
}

// Student Detail Report types
export interface StudentSessionDetail {
  session_id: number;
  session_name: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  was_present: boolean;
  detection_count: number;
  face_crops: Array<{
    id: number;
    image_id: number;
    crop_image_path: string;
    confidence_score: number | null;
    created_at: string;
  }>;
}

export interface StudentDetailReport {
  student: Student;
  statistics: {
    total_sessions: number;
    attended_sessions: number;
    missed_sessions: number;
    attendance_rate: number;
    total_detections: number;
  };
  sessions: StudentSessionDetail[];
}

// Attendance Report types
export interface SessionAttendance {
  session_id: number;
  present: boolean;
  detection_count: number;
}

export interface StudentAttendanceRecord {
  student_id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  student_number: string;
  email: string | null;
  attended_sessions: number;
  total_sessions: number;
  attendance_rate: number;
  session_attendance: SessionAttendance[];
}

export interface SessionSummary {
  id: number;
  name: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  is_processed: boolean;
  present_count: number;
  total_students: number;
  attendance_rate: number;
}

export interface AttendanceReport {
  class_id: number;
  class_name: string;
  total_students: number;
  total_sessions: number;
  date_range: {
    from: string | null;
    to: string | null;
  };
  sessions: SessionSummary[];
  attendance_matrix: StudentAttendanceRecord[];
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
