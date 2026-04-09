import MockAdapter from 'axios-mock-adapter';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import client from '@/api/client';
import {
  createCourse,
  deleteCourse,
  listCourseOfferings,
  listCourses,
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
    mock.onGet('/school/crud/courses').reply(200, [{ id: 1, code: 'MAT406', description: 'Math', level: 4, credits: 4, is_core_or_sanctioned: true, is_active: true }]);

    const courses = await listCourses();
    expect(courses).toHaveLength(1);
    expect(courses[0].code).toBe('MAT406');
  });

  it('creates and deletes a course', async () => {
    mock.onPost('/school/crud/courses').reply(201, {
      id: 2,
      code: 'FRA304',
      description: 'Francais',
      level: 3,
      credits: 4,
      is_core_or_sanctioned: true,
      is_active: true,
    });
    mock.onDelete('/school/crud/courses/2').reply(204);

    const created = await createCourse({
      code: 'FRA304',
      description: 'Francais',
      level: 3,
      credits: 4,
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
});
