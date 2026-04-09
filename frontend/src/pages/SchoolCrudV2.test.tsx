import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SchoolCrudV2 from '@/pages/SchoolCrudV2';
import * as schoolCrud from '@/api/schoolCrud';

vi.mock('@/api/schoolCrud', () => ({
  listCourses: vi.fn(),
  listTeachers: vi.fn(),
  listCourseOfferings: vi.fn(),
  listStudents: vi.fn(),
  createCourse: vi.fn(),
  updateCourse: vi.fn(),
  deleteCourse: vi.fn(),
  createTeacher: vi.fn(),
  updateTeacher: vi.fn(),
  deleteTeacher: vi.fn(),
  createCourseOffering: vi.fn(),
  updateCourseOffering: vi.fn(),
  deleteCourseOffering: vi.fn(),
  createStudent: vi.fn(),
  updateStudent: vi.fn(),
  deleteStudent: vi.fn(),
  getApiErrorMessage: vi.fn(() => 'Erreur'),
}));

describe('SchoolCrudV2', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(schoolCrud.listCourses).mockResolvedValue([
      { id: 1, local_code: 'MAT101', meq_code: null, description: 'Mathématiques', level: 1, credits: 4, periods: 4, is_core_or_sanctioned: true, is_active: true },
      { id: 2, local_code: 'FRA201', meq_code: 'FRA-2', description: 'Français', level: 2, credits: 4, periods: 5, is_core_or_sanctioned: true, is_active: true },
    ]);
    vi.mocked(schoolCrud.listTeachers).mockResolvedValue([
      { id: 10, user: 99, user_email: 'teach@example.com', full_name: 'Mme Alpha', is_active: true },
    ]);
    vi.mocked(schoolCrud.listCourseOfferings).mockResolvedValue([
      { id: 7, course: 2, group_number: '402', academic_year: '2025-2026', teacher: 10, is_active: true },
    ]);
    vi.mocked(schoolCrud.listStudents).mockResolvedValue([
      { fiche: 111, permanent_code: 'AAA111111111', full_name: 'Alice Doe', level: '2', current_group: '201', is_active: true },
      { fiche: 222, permanent_code: 'BBB222222222', full_name: 'Bob Martin', level: '4', current_group: '402', is_active: true },
    ]);
  });

  it('filters courses and students as you type', async () => {
    render(<SchoolCrudV2 />);

    await waitFor(() => expect(screen.getByText('MAT101')).toBeInTheDocument());

    fireEvent.change(screen.getByPlaceholderText('Rechercher un cours'), { target: { value: 'fra' } });
    expect(screen.queryByText('MAT101')).not.toBeInTheDocument();
    expect(screen.getByText('FRA201')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Élèves' }));
    await waitFor(() => expect(screen.getByText('Alice Doe')).toBeInTheDocument());

    fireEvent.change(screen.getByPlaceholderText('Rechercher un élève, groupe ou fiche'), { target: { value: '402' } });
    expect(screen.queryByText('Alice Doe')).not.toBeInTheDocument();
    expect(screen.getByText('Bob Martin')).toBeInTheDocument();
  });
});

