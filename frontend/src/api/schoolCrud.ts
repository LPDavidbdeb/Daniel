import client from './client';

export interface Course {
  id?: number;
  local_code: string;
  meq_code: string | null;
  description: string;
  level: number | null;
  credits: number;
  periods: number;
  is_core_or_sanctioned: boolean;
  is_active: boolean;
}

export interface Teacher {
  id?: number;
  user: number;
  full_name: string;
  is_active: boolean;
  user_email?: string;
}

export interface CourseOffering {
  id?: number;
  course: number;
  group_number: string;
  academic_year: string;
  teacher: number | null;
  is_active: boolean;
}

export interface Cohort {
  id?: number;
  name: string;
  cohort_type: 'ZENITH' | 'IFP' | 'DIM' | 'ACCUEIL' | 'PARCOURS';
  academic_year: string;
  min_capacity: number;
  max_capacity: number;
  is_confirmed: boolean;
}

// --- COURSES ---
export const getCourses = () => client.get<Course[]>('/school/crud/courses');
export const createCourse = (data: Course) => client.post<Course>('/school/crud/courses', data);
// Note: On utilise l'ID technique pour les opérations CRUD car Django Ninja attend l'ID numérique du modèle
export const updateCourse = (id: number, data: Course) => client.put<Course>(`/school/crud/courses/${id}`, data);
export const deleteCourse = (id: number) => client.delete(`/school/crud/courses/${id}`);

// --- TEACHERS ---
export const getTeachers = () => client.get<Teacher[]>('/school/crud/teachers');
export const createTeacher = (data: Teacher) => client.post<Teacher>('/school/crud/teachers', data);
export const updateTeacher = (id: number, data: Teacher) => client.put<Teacher>(`/school/crud/teachers/${id}`, data);
export const deleteTeacher = (id: number) => client.delete(`/school/crud/teachers/${id}`);

// --- OFFERINGS ---
export const getOfferings = () => client.get<CourseOffering[]>('/school/crud/course-offerings');
export const createOffering = (data: CourseOffering) => client.post<CourseOffering>('/school/crud/course-offerings', data);
export const updateOffering = (id: number, data: CourseOffering) => client.put<CourseOffering>(`/school/crud/course-offerings/${id}`, data);
export const deleteOffering = (id: number) => client.delete(`/school/crud/course-offerings/${id}`);

// --- COHORTS ---
export const getCohorts = () => client.get<Cohort[]>('/school/crud/cohorts');
export const createCohort = (data: Cohort) => client.post<Cohort>('/school/crud/cohorts', data);
export const updateCohort = (id: number, data: Cohort) => client.put<Cohort>(`/school/crud/cohorts/${id}`, data);
export const deleteCohort = (id: number) => client.delete(`/school/crud/cohorts/${id}`);
