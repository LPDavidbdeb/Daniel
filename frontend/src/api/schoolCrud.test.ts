import MockAdapter from 'axios-mock-adapter';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import client from '@/api/client';
import {
  createCourse,
  createStudent,
  deleteCourse,
  deleteStudent,
  listCourseOfferings,
  listCourses,
  listStudents,
  updateTeacher,
} from '@/api/schoolCrud';

describe('schoolCrud api', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(client);
  });

  afterEach(() => {
    mock.restore();
  });

  it('lists courses', async () => {
    mock.onGet('/school/crud/courses').reply(200, [{ id: 1, local_code: 'MAT406', meq_code: null, description: 'Math', level: 4, credits: 4, periods: 4, is_core_or_sanctioned: true, is_active: true }]);

    const courses = await listCourses();
    expect(courses).toHaveLength(1);
    expect(courses[0].local_code).toBe('MAT406');
  });

  it('creates and deletes a course', async () => {
    mock.onPost('/school/crud/courses').reply(201, {
      id: 2,
      local_code: 'FRA304',
      meq_code: null,
      description: 'Francais',
      level: 3,
      credits: 4,
      periods: 4,
      is_core_or_sanctioned: true,
      is_active: true,
    });
    mock.onDelete('/school/crud/courses/2').reply(204);

    const created = await createCourse({
      local_code: 'FRA304',
      meq_code: null,
      description: 'Francais',
      level: 3,
      credits: 4,
      periods: 4,
      is_core_or_sanctioned: true,
      is_active: true,
    });

    expect(created.id).toBe(2);

    await expect(deleteCourse(2)).resolves.toBeUndefined();
  });

  it('updates teacher and lists offerings', async () => {
    mock.onPut('/school/crud/teachers/7').reply(200, {
      id: 7,
      user: 99,
      user_email: 'jane@example.com',
      full_name: 'Jane Doe',
      is_active: true,
    });
    mock.onGet('/school/crud/course-offerings').reply(200, [
      {
        id: 3,
        course: 1,
        group_number: '402',
        academic_year: '2025-2026',
        teacher: 7,
        is_active: true,
      },
    ]);

    const teacher = await updateTeacher(7, {
      user: 99,
      full_name: 'Jane Doe',
      is_active: true,
    });
    const offerings = await listCourseOfferings();

    expect(teacher.full_name).toBe('Jane Doe');
    expect(offerings[0].group_number).toBe('402');
  });

  it('lists and mutates students', async () => {
    mock.onGet('/students/crud/students').reply(200, [{
      fiche: 123,
      permanent_code: 'PERM12345678',
      full_name: 'Alice Doe',
      level: '3',
      current_group: '301',
      is_active: true,
    }]);
    mock.onPost('/students/crud/students').reply(201, {
      fiche: 456,
      permanent_code: 'PERM87654321',
      full_name: 'Bob Doe',
      level: '4',
      current_group: '402',
      is_active: true,
    });
    mock.onDelete('/students/crud/students/456').reply(204);

    const students = await listStudents();
    expect(students[0].full_name).toBe('Alice Doe');

    const created = await createStudent({
      fiche: 456,
      permanent_code: 'PERM87654321',
      full_name: 'Bob Doe',
      level: '4',
      current_group: '402',
      is_active: true,
    });
    expect(created.fiche).toBe(456);

    await expect(deleteStudent(456)).resolves.toBeUndefined();
  });
});
