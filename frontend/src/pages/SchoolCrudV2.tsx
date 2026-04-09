import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react';
import { Loader2, Pencil, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';
import {
  SchoolCourse,
  SchoolCourseOffering,
  SchoolStudent,
  SchoolTeacher,
  SchoolCourseOfferingPayload,
  SchoolCoursePayload,
  SchoolStudentPayload,
  SchoolTeacherPayload,
  createCourse,
  createCourseOffering,
  createStudent,
  createTeacher,
  deleteCourse,
  deleteCourseOffering,
  deleteStudent,
  deleteTeacher,
  getApiErrorMessage,
  listCourseOfferings,
  listCourses,
  listStudents,
  listTeachers,
  updateCourse,
  updateCourseOffering,
  updateStudent,
  updateTeacher,
} from '@/api/schoolCrud';

type TabKey = 'courses' | 'teachers' | 'offerings' | 'students';

const initialCourseForm = {
  local_code: '',
  meq_code: '',
  description: '',
  level: '',
  credits: '0',
  periods: '0',
  is_core_or_sanctioned: false,
  is_active: true,
};

const initialTeacherForm = {
  user: '',
  full_name: '',
  is_active: true,
};

const initialOfferingForm = {
  course: '',
  group_number: '',
  academic_year: '2025-2026',
  teacher: '',
  is_active: true,
};

const initialStudentForm = {
  fiche: '',
  permanent_code: '',
  full_name: '',
  level: '',
  current_group: '',
  is_active: true,
};

const normalize = (value: string) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase();

const matches = (haystack: string, query: string) => normalize(haystack).includes(normalize(query));

export default function SchoolCrudV2() {
  const [tab, setTab] = useState<TabKey>('courses');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [courses, setCourses] = useState<SchoolCourse[]>([]);
  const [teachers, setTeachers] = useState<SchoolTeacher[]>([]);
  const [offerings, setOfferings] = useState<SchoolCourseOffering[]>([]);
  const [students, setStudents] = useState<SchoolStudent[]>([]);

  const [courseForm, setCourseForm] = useState(initialCourseForm);
  const [teacherForm, setTeacherForm] = useState(initialTeacherForm);
  const [offeringForm, setOfferingForm] = useState(initialOfferingForm);
  const [studentForm, setStudentForm] = useState(initialStudentForm);

  const [editingCourseId, setEditingCourseId] = useState<number | null>(null);
  const [editingTeacherId, setEditingTeacherId] = useState<number | null>(null);
  const [editingOfferingId, setEditingOfferingId] = useState<number | null>(null);
  const [editingStudentFiche, setEditingStudentFiche] = useState<number | null>(null);

  const [courseSearch, setCourseSearch] = useState('');
  const [teacherSearch, setTeacherSearch] = useState('');
  const [offeringSearch, setOfferingSearch] = useState('');
  const [studentSearch, setStudentSearch] = useState('');

  const courseById = useMemo(() => new Map(courses.map((course) => [course.id, course] as const)), [courses]);
  const teacherById = useMemo(() => new Map(teachers.map((teacher) => [teacher.id, teacher] as const)), [teachers]);

  const filteredCourses = useMemo(
    () => courses.filter((course) => !courseSearch || [course.local_code, course.meq_code ?? '', course.description, String(course.level ?? ''), String(course.credits), String(course.periods)]
      .some((item) => matches(item, courseSearch))),
    [courses, courseSearch],
  );

  const filteredTeachers = useMemo(
    () => teachers.filter((teacher) => !teacherSearch || [teacher.full_name, teacher.user_email, String(teacher.user)]
      .some((item) => matches(item, teacherSearch))),
    [teachers, teacherSearch],
  );

  const filteredOfferings = useMemo(
    () => offerings.filter((offering) => {
      if (!offeringSearch) return true;
      const course = courseById.get(offering.course);
      const teacher = teacherById.get(offering.teacher ?? -1);
      return [
        course?.local_code ?? '',
        course?.description ?? '',
        offering.group_number,
        offering.academic_year,
        teacher?.full_name ?? '',
        teacher?.user_email ?? '',
      ].some((item) => matches(item, offeringSearch));
    }),
    [offerings, offeringSearch, courseById, teacherById],
  );

  const filteredStudents = useMemo(
    () => students.filter((student) => !studentSearch || [student.fiche, student.permanent_code, student.full_name, student.level, student.current_group]
      .map(String)
      .some((item) => matches(item, studentSearch))),
    [students, studentSearch],
  );

  const loadAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [coursesData, teachersData, offeringsData, studentsData] = await Promise.all([
        listCourses(),
        listTeachers(),
        listCourseOfferings(),
        listStudents(),
      ]);
      setCourses(coursesData);
      setTeachers(teachersData);
      setOfferings(offeringsData);
      setStudents(studentsData);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const clearFeedback = () => {
    setError('');
    setSuccess('');
  };

  const resetCourseForm = () => {
    setCourseForm(initialCourseForm);
    setEditingCourseId(null);
  };

  const resetTeacherForm = () => {
    setTeacherForm(initialTeacherForm);
    setEditingTeacherId(null);
  };

  const resetOfferingForm = () => {
    setOfferingForm(initialOfferingForm);
    setEditingOfferingId(null);
  };

  const resetStudentForm = () => {
    setStudentForm(initialStudentForm);
    setEditingStudentFiche(null);
  };

  const handleCourseSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearFeedback();
    setSaving(true);
    try {
      const payload: SchoolCoursePayload = {
        local_code: courseForm.local_code.trim(),
        meq_code: courseForm.meq_code.trim() || null,
        description: courseForm.description.trim(),
        level: courseForm.level ? Number(courseForm.level) : null,
        credits: Number(courseForm.credits),
        periods: Number(courseForm.periods),
        is_core_or_sanctioned: courseForm.is_core_or_sanctioned,
        is_active: courseForm.is_active,
      };
      if (editingCourseId === null) {
        await createCourse(payload);
        setSuccess('Cours cree.');
      } else {
        await updateCourse(editingCourseId, payload);
        setSuccess('Cours mis a jour.');
      }
      await loadAll();
      resetCourseForm();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleTeacherSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearFeedback();
    if (!teacherForm.user) {
      setError('Le champ User ID est requis.');
      return;
    }
    setSaving(true);
    try {
      const payload: SchoolTeacherPayload = {
        user: Number(teacherForm.user),
        full_name: teacherForm.full_name.trim(),
        is_active: teacherForm.is_active,
      };
      if (editingTeacherId === null) {
        await createTeacher(payload);
        setSuccess('Enseignant cree.');
      } else {
        await updateTeacher(editingTeacherId, payload);
        setSuccess('Enseignant mis a jour.');
      }
      await loadAll();
      resetTeacherForm();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleOfferingSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearFeedback();
    if (!offeringForm.course) {
      setError('Selectionnez un cours.');
      return;
    }
    setSaving(true);
    try {
      const payload: SchoolCourseOfferingPayload = {
        course: Number(offeringForm.course),
        group_number: offeringForm.group_number.trim(),
        academic_year: offeringForm.academic_year.trim(),
        teacher: offeringForm.teacher ? Number(offeringForm.teacher) : null,
        is_active: offeringForm.is_active,
      };
      if (editingOfferingId === null) {
        await createCourseOffering(payload);
        setSuccess('Groupe cree.');
      } else {
        await updateCourseOffering(editingOfferingId, payload);
        setSuccess('Groupe mis a jour.');
      }
      await loadAll();
      resetOfferingForm();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleStudentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearFeedback();
    setSaving(true);
    try {
      if (!studentForm.fiche) {
        setError('La fiche est requise.');
        return;
      }
      const payload: SchoolStudentPayload = {
        fiche: Number(studentForm.fiche),
        permanent_code: studentForm.permanent_code.trim(),
        full_name: studentForm.full_name.trim(),
        level: studentForm.level.trim(),
        current_group: studentForm.current_group.trim(),
        is_active: studentForm.is_active,
      };
      if (editingStudentFiche === null) {
        await createStudent(payload);
        setSuccess('Eleve cree.');
      } else {
        await updateStudent(editingStudentFiche, payload);
        setSuccess('Eleve mis a jour.');
      }
      await loadAll();
      resetStudentForm();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (kind: 'course' | 'teacher' | 'offering' | 'student', id: number) => {
    if (!window.confirm('Confirmer la suppression?')) return;
    clearFeedback();
    setSaving(true);
    try {
      if (kind === 'course') await deleteCourse(id);
      if (kind === 'teacher') await deleteTeacher(id);
      if (kind === 'offering') await deleteCourseOffering(id);
      if (kind === 'student') await deleteStudent(id);
      setSuccess('Suppression terminee.');
      await loadAll();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-100 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestion School</h1>
          <p className="text-sm text-gray-600">Recherche live et CRUD pour cours, enseignants, groupes et élèves.</p>
        </div>
        <button
          type="button"
          onClick={loadAll}
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-70"
        >
          <RefreshCw className="h-4 w-4" />
          Rafraichir
        </button>
      </div>

      {error && <div className="rounded-lg bg-red-100 p-3 text-sm text-red-700">{error}</div>}
      {success && <div className="rounded-lg bg-green-100 p-3 text-sm text-green-700">{success}</div>}

      <div className="flex flex-wrap gap-2">
        {([
          ['courses', 'Cours'],
          ['teachers', 'Enseignants'],
          ['offerings', 'Groupes'],
          ['students', 'Élèves'],
        ] as Array<[TabKey, string]>).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`rounded-lg px-3 py-2 text-sm font-semibold ${tab === key ? 'bg-blue-600 text-white' : 'border border-gray-200 bg-white text-gray-700'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'courses' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <form onSubmit={handleCourseSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingCourseId ? 'Modifier un cours' : 'Nouveau cours'}</h2>
            <Input label="Code local" value={courseForm.local_code} onChange={(value) => setCourseForm((prev) => ({ ...prev, local_code: value }))} required />
            <Input label="Code MEQ" value={courseForm.meq_code} onChange={(value) => setCourseForm((prev) => ({ ...prev, meq_code: value }))} />
            <Input label="Description" value={courseForm.description} onChange={(value) => setCourseForm((prev) => ({ ...prev, description: value }))} required />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Niveau" type="number" value={courseForm.level} onChange={(value) => setCourseForm((prev) => ({ ...prev, level: value }))} min={1} max={5} />
              <Input label="Crédits" type="number" value={courseForm.credits} onChange={(value) => setCourseForm((prev) => ({ ...prev, credits: value }))} min={0} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input label="Périodes" type="number" value={courseForm.periods} onChange={(value) => setCourseForm((prev) => ({ ...prev, periods: value }))} min={0} required />
              <div />
            </div>
            <Checkbox label="Matière de base / sanctionnée" checked={courseForm.is_core_or_sanctioned} onChange={(checked) => setCourseForm((prev) => ({ ...prev, is_core_or_sanctioned: checked }))} />
            <Checkbox label="Actif" checked={courseForm.is_active} onChange={(checked) => setCourseForm((prev) => ({ ...prev, is_active: checked }))} />
            <ActionRow saving={saving} editing={editingCourseId !== null} onCancel={resetCourseForm} />
          </form>

          <ListPanel
            title="Liste des cours"
            search={courseSearch}
            onSearch={setCourseSearch}
            placeholder="Rechercher un cours"
            count={filteredCourses.length}
          >
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500">
                <tr>
                  <th className="py-2">Code</th>
                  <th className="py-2">Description</th>
                  <th className="py-2">MEQ</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredCourses.map((course) => (
                  <tr key={course.id} className="border-t border-gray-100">
                    <td className="py-2 font-medium">{course.local_code}</td>
                    <td className="py-2">{course.description}</td>
                    <td className="py-2">{course.meq_code ?? '-'}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <IconButton
                          label="Edit"
                          onClick={() => {
                            setEditingCourseId(course.id);
                            setCourseForm({
                              local_code: course.local_code,
                              meq_code: course.meq_code ?? '',
                              description: course.description,
                              level: course.level === null ? '' : String(course.level),
                              credits: String(course.credits),
                              periods: String(course.periods),
                              is_core_or_sanctioned: course.is_core_or_sanctioned,
                              is_active: course.is_active,
                            });
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </IconButton>
                        <IconButton label="Supprimer" destructive onClick={() => handleDelete('course', course.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </IconButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ListPanel>
        </div>
      )}

      {tab === 'teachers' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <form onSubmit={handleTeacherSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingTeacherId ? 'Modifier un enseignant' : 'Nouvel enseignant'}</h2>
            <Input label="User ID" type="number" value={teacherForm.user} onChange={(value) => setTeacherForm((prev) => ({ ...prev, user: value }))} required />
            <Input label="Nom complet" value={teacherForm.full_name} onChange={(value) => setTeacherForm((prev) => ({ ...prev, full_name: value }))} required />
            <Checkbox label="Actif" checked={teacherForm.is_active} onChange={(checked) => setTeacherForm((prev) => ({ ...prev, is_active: checked }))} />
            <ActionRow saving={saving} editing={editingTeacherId !== null} onCancel={resetTeacherForm} />
          </form>

          <ListPanel
            title="Liste des enseignants"
            search={teacherSearch}
            onSearch={setTeacherSearch}
            placeholder="Rechercher un prof"
            count={filteredTeachers.length}
          >
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500">
                <tr>
                  <th className="py-2">Nom</th>
                  <th className="py-2">Email</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTeachers.map((teacher) => (
                  <tr key={teacher.id} className="border-t border-gray-100">
                    <td className="py-2 font-medium">{teacher.full_name}</td>
                    <td className="py-2">{teacher.user_email}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <IconButton
                          label="Edit"
                          onClick={() => {
                            setEditingTeacherId(teacher.id);
                            setTeacherForm({ user: String(teacher.user), full_name: teacher.full_name, is_active: teacher.is_active });
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </IconButton>
                        <IconButton label="Supprimer" destructive onClick={() => handleDelete('teacher', teacher.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </IconButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ListPanel>
        </div>
      )}

      {tab === 'offerings' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <form onSubmit={handleOfferingSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingOfferingId ? 'Modifier un groupe' : 'Nouveau groupe'}</h2>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="offering-course">Cours</label>
              <select id="offering-course" required value={offeringForm.course} onChange={(e) => setOfferingForm((prev) => ({ ...prev, course: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2">
                <option value="">Sélectionner</option>
                {courses.map((course) => (
                  <option key={course.id} value={String(course.id)}>{course.local_code} - {course.description}</option>
                ))}
              </select>
            </div>
            <Input label="Numéro de groupe" value={offeringForm.group_number} onChange={(value) => setOfferingForm((prev) => ({ ...prev, group_number: value }))} required />
            <Input label="Année scolaire" value={offeringForm.academic_year} onChange={(value) => setOfferingForm((prev) => ({ ...prev, academic_year: value }))} required />
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="offering-teacher">Enseignant</label>
              <select id="offering-teacher" value={offeringForm.teacher} onChange={(e) => setOfferingForm((prev) => ({ ...prev, teacher: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2">
                <option value="">Aucun</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={String(teacher.id)}>{teacher.full_name}</option>
                ))}
              </select>
            </div>
            <Checkbox label="Actif" checked={offeringForm.is_active} onChange={(checked) => setOfferingForm((prev) => ({ ...prev, is_active: checked }))} />
            <ActionRow saving={saving} editing={editingOfferingId !== null} onCancel={resetOfferingForm} />
          </form>

          <ListPanel
            title="Liste des groupes"
            search={offeringSearch}
            onSearch={setOfferingSearch}
            placeholder="Rechercher un cours, prof ou groupe"
            count={filteredOfferings.length}
          >
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500">
                <tr>
                  <th className="py-2">Cours</th>
                  <th className="py-2">Groupe</th>
                  <th className="py-2">Prof</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredOfferings.map((offering) => {
                  const course = courseById.get(offering.course);
                  const teacher = offering.teacher ? teacherById.get(offering.teacher) : null;
                  return (
                    <tr key={offering.id} className="border-t border-gray-100">
                      <td className="py-2">{course?.local_code ?? offering.course}</td>
                      <td className="py-2">{offering.group_number}</td>
                      <td className="py-2">{teacher?.full_name ?? '-'}</td>
                      <td className="py-2">
                        <div className="flex gap-2">
                          <IconButton
                            label="Edit"
                            onClick={() => {
                              setEditingOfferingId(offering.id);
                              setOfferingForm({
                                course: String(offering.course),
                                group_number: offering.group_number,
                                academic_year: offering.academic_year,
                                teacher: offering.teacher === null ? '' : String(offering.teacher),
                                is_active: offering.is_active,
                              });
                            }}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </IconButton>
                          <IconButton label="Supprimer" destructive onClick={() => handleDelete('offering', offering.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </IconButton>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </ListPanel>
        </div>
      )}

      {tab === 'students' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <form onSubmit={handleStudentSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingStudentFiche ? 'Modifier un élève' : 'Nouvel élève'}</h2>
            <Input label="Fiche" type="number" value={studentForm.fiche} onChange={(value) => setStudentForm((prev) => ({ ...prev, fiche: value }))} required disabled={editingStudentFiche !== null} />
            <Input label="Code permanent" value={studentForm.permanent_code} onChange={(value) => setStudentForm((prev) => ({ ...prev, permanent_code: value }))} required />
            <Input label="Nom complet" value={studentForm.full_name} onChange={(value) => setStudentForm((prev) => ({ ...prev, full_name: value }))} required />
            <Input label="Niveau" value={studentForm.level} onChange={(value) => setStudentForm((prev) => ({ ...prev, level: value }))} required />
            <Input label="Groupe actuel" value={studentForm.current_group} onChange={(value) => setStudentForm((prev) => ({ ...prev, current_group: value }))} required />
            <Checkbox label="Actif" checked={studentForm.is_active} onChange={(checked) => setStudentForm((prev) => ({ ...prev, is_active: checked }))} />
            <ActionRow saving={saving} editing={editingStudentFiche !== null} onCancel={resetStudentForm} />
          </form>

          <ListPanel
            title="Liste des élèves"
            search={studentSearch}
            onSearch={setStudentSearch}
            placeholder="Rechercher un élève, groupe ou fiche"
            count={filteredStudents.length}
          >
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500">
                <tr>
                  <th className="py-2">Fiche</th>
                  <th className="py-2">Nom</th>
                  <th className="py-2">Groupe</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((student) => (
                  <tr key={student.fiche} className="border-t border-gray-100">
                    <td className="py-2 font-medium">{student.fiche}</td>
                    <td className="py-2">{student.full_name}</td>
                    <td className="py-2">{student.current_group}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <IconButton
                          label="Edit"
                          onClick={() => {
                            setEditingStudentFiche(student.fiche);
                            setStudentForm({
                              fiche: String(student.fiche),
                              permanent_code: student.permanent_code,
                              full_name: student.full_name,
                              level: student.level,
                              current_group: student.current_group,
                              is_active: student.is_active,
                            });
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </IconButton>
                        <IconButton label="Supprimer" destructive onClick={() => handleDelete('student', student.fiche)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </IconButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ListPanel>
        </div>
      )}
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
  min,
  max,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  min?: number;
  max?: number;
  disabled?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        min={min}
        max={max}
        disabled={disabled}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 disabled:bg-gray-50"
      />
    </div>
  );
}

function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-gray-700">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

function ActionRow({
  saving,
  editing,
  onCancel,
}: {
  saving: boolean;
  editing: boolean;
  onCancel: () => void;
}) {
  return (
    <div className="flex gap-2">
      <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70">
        <Plus className="h-4 w-4" />
        {editing ? 'Mettre à jour' : 'Créer'}
      </button>
      {editing && (
        <button type="button" onClick={onCancel} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Annuler
        </button>
      )}
    </div>
  );
}

function ListPanel({
  title,
  search,
  onSearch,
  placeholder,
  count,
  children,
}: {
  title: string;
  search: string;
  onSearch: (value: string) => void;
  placeholder: string;
  count: number;
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <p className="text-xs text-gray-500">{count} résultat(s)</p>
        </div>
        <div className="relative w-full max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder={placeholder}
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm"
          />
        </div>
      </div>
      <div className="overflow-auto">{children}</div>
    </div>
  );
}

function IconButton({
  label,
  destructive = false,
  onClick,
  children,
}: {
  label: string;
  destructive?: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-xs ${destructive ? 'border-red-200 text-red-700 hover:bg-red-50' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}
    >
      {children}
    </button>
  );
}


