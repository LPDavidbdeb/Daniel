import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Loader2, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react';
import {
  SchoolCourse,
  SchoolCourseOffering,
  SchoolTeacher,
  SchoolCourseOfferingPayload,
  SchoolCoursePayload,
  SchoolTeacherPayload,
  createCourse,
  createCourseOffering,
  createTeacher,
  deleteCourse,
  deleteCourseOffering,
  deleteTeacher,
  getApiErrorMessage,
  listCourseOfferings,
  listCourses,
  listTeachers,
  updateCourse,
  updateCourseOffering,
  updateTeacher,
} from '@/api/schoolCrud';

type TabKey = 'courses' | 'teachers' | 'offerings';

const initialCourseForm = {
  code: '',
  description: '',
  level: '',
  credits: '0',
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

const SchoolCrud = () => {
  const [tab, setTab] = useState<TabKey>('courses');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [courses, setCourses] = useState<SchoolCourse[]>([]);
  const [teachers, setTeachers] = useState<SchoolTeacher[]>([]);
  const [offerings, setOfferings] = useState<SchoolCourseOffering[]>([]);

  const [courseForm, setCourseForm] = useState(initialCourseForm);
  const [teacherForm, setTeacherForm] = useState(initialTeacherForm);
  const [offeringForm, setOfferingForm] = useState(initialOfferingForm);

  const [editingCourseId, setEditingCourseId] = useState<number | null>(null);
  const [editingTeacherId, setEditingTeacherId] = useState<number | null>(null);
  const [editingOfferingId, setEditingOfferingId] = useState<number | null>(null);

  const courseById = useMemo(() => {
    const map = new Map<number, SchoolCourse>();
    courses.forEach((course) => map.set(course.id, course));
    return map;
  }, [courses]);

  const teacherById = useMemo(() => {
    const map = new Map<number, SchoolTeacher>();
    teachers.forEach((teacher) => map.set(teacher.id, teacher));
    return map;
  }, [teachers]);

  const loadAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [coursesData, teachersData, offeringsData] = await Promise.all([
        listCourses(),
        listTeachers(),
        listCourseOfferings(),
      ]);
      setCourses(coursesData);
      setTeachers(teachersData);
      setOfferings(offeringsData);
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

  const handleCourseSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearFeedback();
    setSaving(true);

    try {
      const payload: SchoolCoursePayload = {
        code: courseForm.code.trim(),
        description: courseForm.description.trim(),
        level: courseForm.level ? Number(courseForm.level) : null,
        credits: Number(courseForm.credits),
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

  const handleDelete = async (entity: 'course' | 'teacher' | 'offering', id: number) => {
    const confirmed = window.confirm('Confirmer la suppression?');
    if (!confirmed) {
      return;
    }

    clearFeedback();
    setSaving(true);

    try {
      if (entity === 'course') {
        await deleteCourse(id);
        if (editingCourseId === id) {
          resetCourseForm();
        }
      } else if (entity === 'teacher') {
        await deleteTeacher(id);
        if (editingTeacherId === id) {
          resetTeacherForm();
        }
      } else {
        await deleteCourseOffering(id);
        if (editingOfferingId === id) {
          resetOfferingForm();
        }
      }
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
      <div className="flex items-center justify-center min-h-100">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestion School</h1>
          <p className="text-sm text-gray-600">CRUD pour cours, enseignants et groupes.</p>
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

      <div className="flex gap-2">
        {([
          ['courses', 'Cours'],
          ['teachers', 'Enseignants'],
          ['offerings', 'Groupes'],
        ] as Array<[TabKey, string]>).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`rounded-lg px-3 py-2 text-sm font-semibold ${tab === key ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-200'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'courses' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={handleCourseSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingCourseId ? 'Modifier un cours' : 'Nouveau cours'}</h2>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="course-code">Code</label>
              <input id="course-code" required value={courseForm.code} onChange={(e) => setCourseForm((prev) => ({ ...prev, code: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="course-description">Description</label>
              <input id="course-description" required value={courseForm.description} onChange={(e) => setCourseForm((prev) => ({ ...prev, description: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="course-level">Niveau</label>
                <input id="course-level" type="number" min={1} max={5} value={courseForm.level} onChange={(e) => setCourseForm((prev) => ({ ...prev, level: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="course-credits">Credits</label>
                <input id="course-credits" type="number" min={0} required value={courseForm.credits} onChange={(e) => setCourseForm((prev) => ({ ...prev, credits: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={courseForm.is_core_or_sanctioned} onChange={(e) => setCourseForm((prev) => ({ ...prev, is_core_or_sanctioned: e.target.checked }))} />
              Matiere de base / sanctionnee
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={courseForm.is_active} onChange={(e) => setCourseForm((prev) => ({ ...prev, is_active: e.target.checked }))} />
              Actif
            </label>
            <div className="flex gap-2">
              <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70">
                <Plus className="h-4 w-4" />
                {editingCourseId ? 'Mettre a jour' : 'Creer'}
              </button>
              {editingCourseId !== null && (
                <button type="button" onClick={resetCourseForm} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Annuler
                </button>
              )}
            </div>
          </form>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Liste des cours</h2>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-gray-500">
                  <tr>
                    <th className="py-2">Code</th>
                    <th className="py-2">Description</th>
                    <th className="py-2">Niveau</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {courses.map((course) => (
                    <tr key={course.id} className="border-t border-gray-100">
                      <td className="py-2 font-medium">{course.code}</td>
                      <td className="py-2">{course.description}</td>
                      <td className="py-2">{course.level ?? '-'}</td>
                      <td className="py-2">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              setEditingCourseId(course.id);
                              setCourseForm({
                                code: course.code,
                                description: course.description,
                                level: course.level === null ? '' : String(course.level),
                                credits: String(course.credits),
                                is_core_or_sanctioned: course.is_core_or_sanctioned,
                                is_active: course.is_active,
                              });
                            }}
                            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                          >
                            <Pencil className="h-3.5 w-3.5" /> Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete('course', course.id)}
                            className="inline-flex items-center gap-1 rounded border border-red-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-3.5 w-3.5" /> Supprimer
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === 'teachers' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={handleTeacherSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingTeacherId ? 'Modifier un enseignant' : 'Nouvel enseignant'}</h2>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="teacher-user">User ID</label>
              <input id="teacher-user" type="number" required value={teacherForm.user} onChange={(e) => setTeacherForm((prev) => ({ ...prev, user: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="teacher-name">Nom complet</label>
              <input id="teacher-name" required value={teacherForm.full_name} onChange={(e) => setTeacherForm((prev) => ({ ...prev, full_name: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={teacherForm.is_active} onChange={(e) => setTeacherForm((prev) => ({ ...prev, is_active: e.target.checked }))} />
              Actif
            </label>
            <div className="flex gap-2">
              <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70">
                <Plus className="h-4 w-4" />
                {editingTeacherId ? 'Mettre a jour' : 'Creer'}
              </button>
              {editingTeacherId !== null && (
                <button type="button" onClick={resetTeacherForm} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Annuler
                </button>
              )}
            </div>
          </form>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Liste des enseignants</h2>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-gray-500">
                  <tr>
                    <th className="py-2">ID</th>
                    <th className="py-2">Nom</th>
                    <th className="py-2">Actif</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {teachers.map((teacher) => (
                    <tr key={teacher.id} className="border-t border-gray-100">
                      <td className="py-2">{teacher.id}</td>
                      <td className="py-2 font-medium">{teacher.full_name}</td>
                      <td className="py-2">{teacher.is_active ? 'Oui' : 'Non'}</td>
                      <td className="py-2">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              setEditingTeacherId(teacher.id);
                              setTeacherForm({
                                user: teacher.user === null ? '' : String(teacher.user),
                                full_name: teacher.full_name,
                                is_active: teacher.is_active,
                              });
                            }}
                            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                          >
                            <Pencil className="h-3.5 w-3.5" /> Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete('teacher', teacher.id)}
                            className="inline-flex items-center gap-1 rounded border border-red-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-3.5 w-3.5" /> Supprimer
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === 'offerings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={handleOfferingSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">{editingOfferingId ? 'Modifier un groupe' : 'Nouveau groupe'}</h2>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="offering-course">Cours</label>
              <select id="offering-course" required value={offeringForm.course} onChange={(e) => setOfferingForm((prev) => ({ ...prev, course: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2">
                <option value="">Selectionner</option>
                {courses.map((course) => (
                  <option key={course.id} value={String(course.id)}>{course.code} - {course.description}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="offering-group">Numero de groupe</label>
              <input id="offering-group" required value={offeringForm.group_number} onChange={(e) => setOfferingForm((prev) => ({ ...prev, group_number: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="offering-year">Annee scolaire</label>
              <input id="offering-year" required value={offeringForm.academic_year} onChange={(e) => setOfferingForm((prev) => ({ ...prev, academic_year: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="offering-teacher">Enseignant</label>
              <select id="offering-teacher" value={offeringForm.teacher} onChange={(e) => setOfferingForm((prev) => ({ ...prev, teacher: e.target.value }))} className="w-full rounded-lg border border-gray-300 px-3 py-2">
                <option value="">Aucun</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={String(teacher.id)}>{teacher.full_name}</option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={offeringForm.is_active} onChange={(e) => setOfferingForm((prev) => ({ ...prev, is_active: e.target.checked }))} />
              Actif
            </label>
            <div className="flex gap-2">
              <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-70">
                <Plus className="h-4 w-4" />
                {editingOfferingId ? 'Mettre a jour' : 'Creer'}
              </button>
              {editingOfferingId !== null && (
                <button type="button" onClick={resetOfferingForm} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Annuler
                </button>
              )}
            </div>
          </form>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Liste des groupes</h2>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-gray-500">
                  <tr>
                    <th className="py-2">Cours</th>
                    <th className="py-2">Groupe</th>
                    <th className="py-2">Annee</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {offerings.map((offering) => (
                    <tr key={offering.id} className="border-t border-gray-100">
                      <td className="py-2">{courseById.get(offering.course)?.code ?? offering.course}</td>
                      <td className="py-2">{offering.group_number}</td>
                      <td className="py-2">{offering.academic_year}</td>
                      <td className="py-2">
                        <div className="flex gap-2">
                          <button
                            type="button"
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
                            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                          >
                            <Pencil className="h-3.5 w-3.5" /> Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete('offering', offering.id)}
                            className="inline-flex items-center gap-1 rounded border border-red-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-3.5 w-3.5" /> Supprimer
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-gray-500">
              Enseignant: affiche via ID; details disponibles dans les pages de consultation existantes.
              {teacherById.size > 0 ? '' : ' Aucun enseignant charge.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchoolCrud;

