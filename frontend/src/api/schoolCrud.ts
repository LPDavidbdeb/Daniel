import axios from 'axios';
import client from '@/api/client';

export interface SchoolCourse {
  id: number;
  code: string;
  description: string;
  level: number | null;
  credits: number;
  is_core_or_sanctioned: boolean;
  is_active: boolean;
}

export interface SchoolTeacher {
  id: number;
  user: number | null;
  full_name: string;
  is_active: boolean;
}

export interface SchoolCourseOffering {
  id: number;
  course: number;
  group_number: string;
  academic_year: string;
  teacher: number | null;
  is_active: boolean;
}

export type SchoolCoursePayload = Omit<SchoolCourse, 'id'>;
export type SchoolTeacherPayload = Omit<SchoolTeacher, 'id'>;
export type SchoolCourseOfferingPayload = Omit<SchoolCourseOffering, 'id'>;

export async function listCourses(): Promise<SchoolCourse[]> {
  const response = await client.get<SchoolCourse[]>('/school/crud/courses');
  return response.data;
}

export async function createCourse(payload: SchoolCoursePayload): Promise<SchoolCourse> {
  const response = await client.post<SchoolCourse>('/school/crud/courses', payload);
  return response.data;
}

export async function updateCourse(id: number, payload: SchoolCoursePayload): Promise<SchoolCourse> {
  const response = await client.put<SchoolCourse>(`/school/crud/courses/${id}`, payload);
  return response.data;
}

export async function deleteCourse(id: number): Promise<void> {
  await client.delete(`/school/crud/courses/${id}`);
}

export async function listTeachers(): Promise<SchoolTeacher[]> {
  const response = await client.get<SchoolTeacher[]>('/school/crud/teachers');
  return response.data;
}

export async function createTeacher(payload: SchoolTeacherPayload): Promise<SchoolTeacher> {
  const response = await client.post<SchoolTeacher>('/school/crud/teachers', payload);
  return response.data;
}

export async function updateTeacher(id: number, payload: SchoolTeacherPayload): Promise<SchoolTeacher> {
  const response = await client.put<SchoolTeacher>(`/school/crud/teachers/${id}`, payload);
  return response.data;
}

export async function deleteTeacher(id: number): Promise<void> {
  await client.delete(`/school/crud/teachers/${id}`);
}

export async function listCourseOfferings(): Promise<SchoolCourseOffering[]> {
  const response = await client.get<SchoolCourseOffering[]>('/school/crud/course-offerings');
  return response.data;
}

export async function createCourseOffering(payload: SchoolCourseOfferingPayload): Promise<SchoolCourseOffering> {
  const response = await client.post<SchoolCourseOffering>('/school/crud/course-offerings', payload);
  return response.data;
}

export async function updateCourseOffering(
  id: number,
  payload: SchoolCourseOfferingPayload,
): Promise<SchoolCourseOffering> {
  const response = await client.put<SchoolCourseOffering>(`/school/crud/course-offerings/${id}`, payload);
  return response.data;
}

export async function deleteCourseOffering(id: number): Promise<void> {
  await client.delete(`/school/crud/course-offerings/${id}`);
}

export function getApiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return 'Erreur inattendue.';
  }
  if (!error.response) {
    return 'Impossible de joindre l API.';
  }

  const detail = error.response.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail.join(' | ');
  }

  if (detail && typeof detail === 'object') {
    const entries = Object.entries(detail as Record<string, unknown>);
    if (entries.length > 0) {
      return entries
        .map(([key, value]) => `${key}: ${String(value)}`)
        .join(' | ');
    }
  }

  return 'Erreur serveur.';
}
