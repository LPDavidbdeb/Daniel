import axios, { AxiosResponse } from 'axios';
import client from './client';

export interface Course {
  id: number;
  local_code: string;
  meq_code: string | null;
  description: string;
  level: number | null;
  credits: number;
  periods: number;
  is_core_or_sanctioned: boolean;
  stream: 'REGULAR' | 'ZENITH' | 'IFP' | 'ACCUEIL';
  category: 'CORE' | 'PARCOURS' | 'OPTION';
  cycle: 'PREMIER' | 'DEUXIEME' | 'ACCUEIL';
  group_type: 'OPEN' | 'CLOSED';
  is_active: boolean;
}

export interface Teacher {
  id: number;
  user: number;
  full_name: string;
  is_active: boolean;
  user_email: string;
}

export interface CourseOffering {
  id: number;
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

export interface Evaluation {
  student_id: number;
  academic_year: string;
  total_credits_accumulated: number;
  core_failures_count: number;
  borderline_count: number;
  recommendation: 'PROMOTE' | 'RETAIN' | 'TRANSFER_IFP';
  confidence: 'HIGH' | 'LOW';
  requires_review: boolean;
}

export interface Student {
  fiche: number;
  permanent_code: string;
  full_name: string;
  level: string;
  current_group: string;
  is_active: boolean;
}

// Backward-compatible aliases used by SchoolCrudV2.
export type SchoolCourse = Course;
export type SchoolTeacher = Teacher;
export type SchoolCourseOffering = CourseOffering;
export type SchoolStudent = Student;
export type SchoolCoursePayload = Omit<Course, 'id'>;
export type SchoolTeacherPayload = Omit<Teacher, 'id' | 'user_email'>;
export type SchoolCourseOfferingPayload = Omit<CourseOffering, 'id'>;
export type SchoolStudentPayload = Student;

const unwrap = <T>(request: Promise<AxiosResponse<T>>) => request.then((response) => response.data);

// --- COURSES ---
export const listCourses = () => unwrap(client.get<Course[]>('/school/crud/courses'));
export const getCourses = listCourses;
export const createCourse = (data: SchoolCoursePayload) => unwrap(client.post<Course>('/school/crud/courses', data));
export const updateCourse = (id: number, data: SchoolCoursePayload) => unwrap(client.put<Course>(`/school/crud/courses/${id}`, data));
export const deleteCourse = (id: number) => client.delete(`/school/crud/courses/${id}`).then(() => undefined);

// --- TEACHERS ---
export const listTeachers = () => unwrap(client.get<Teacher[]>('/school/crud/teachers'));
export const getTeachers = listTeachers;
export const createTeacher = (data: SchoolTeacherPayload) => unwrap(client.post<Teacher>('/school/crud/teachers', data));
export const updateTeacher = (id: number, data: SchoolTeacherPayload) => unwrap(client.put<Teacher>(`/school/crud/teachers/${id}`, data));
export const deleteTeacher = (id: number) => client.delete(`/school/crud/teachers/${id}`).then(() => undefined);

// --- OFFERINGS ---
export const listCourseOfferings = () => unwrap(client.get<CourseOffering[]>('/school/crud/course-offerings'));
export const getOfferings = listCourseOfferings;
export const createOffering = (data: SchoolCourseOfferingPayload) => unwrap(client.post<CourseOffering>('/school/crud/course-offerings', data));
export const updateOffering = (id: number, data: SchoolCourseOfferingPayload) => unwrap(client.put<CourseOffering>(`/school/crud/course-offerings/${id}`, data));
export const deleteOffering = (id: number) => client.delete(`/school/crud/course-offerings/${id}`).then(() => undefined);
export const createCourseOffering = createOffering;
export const updateCourseOffering = updateOffering;
export const deleteCourseOffering = deleteOffering;

// --- STUDENTS ---
export const listStudents = () => unwrap(client.get<Student[]>('/students/crud/students'));
export const createStudent = (data: SchoolStudentPayload) => unwrap(client.post<Student>('/students/crud/students', data));
export const updateStudent = (fiche: number, data: SchoolStudentPayload) => unwrap(client.put<Student>(`/students/crud/students/${fiche}`, data));
export const deleteStudent = (fiche: number) => client.delete(`/students/crud/students/${fiche}`).then(() => undefined);

// --- COHORTS ---
export const listCohorts = () => unwrap(client.get<Cohort[]>('/school/crud/cohorts'));
export const getCohorts = listCohorts;
export const createCohort = (data: Cohort) => unwrap(client.post<Cohort>('/school/crud/cohorts', data));
export const updateCohort = (id: number, data: Cohort) => unwrap(client.put<Cohort>(`/school/crud/cohorts/${id}`, data));
export const deleteCohort = (id: number) => client.delete(`/school/crud/cohorts/${id}`).then(() => undefined);

// --- EVALUATIONS ---
export const getStudentEvaluation = (fiche: number | string, year?: string) =>
  unwrap(client.get<Evaluation>(`/students/${fiche}/evaluation${year ? `?year=${year}` : ''}`));

export const getApiErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (typeof error.message === 'string' && error.message.trim()) {
      return error.message;
    }
    return `Erreur API (${error.response?.status ?? 'inconnue'})`;
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return 'Une erreur inconnue est survenue.';
};
