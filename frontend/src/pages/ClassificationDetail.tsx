import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Loader2, Sun, X } from 'lucide-react';
import client from '@/api/client';

// ── Classification metadata ───────────────────────────────────────────────────

interface ClassInfo {
  label: string;
  badge: string;         // Tailwind classes for the badge
  criteria: string;      // Short rule shown in the header
  explanation: string;   // Human-readable explanation
}

const CLASS_INFO: Record<string, ClassInfo> = {
  ALL: {
    label: 'Tous les élèves inscrits',
    badge: 'bg-gray-100 text-gray-700 border-gray-300',
    criteria: 'Tous',
    explanation: 'Ensemble des élèves ayant un résultat enregistré pour ce cours, quelle que soit leur note.',
  },
  CERTAIN_PASS: {
    label: 'Passe — crédits acquis',
    badge: 'bg-green-100 text-green-800 border-green-300',
    criteria: 'Note finale ≥ 60',
    explanation:
      'L\'élève a atteint le seuil de réussite. Les crédits du cours sont acquis. ' +
      'Aucune action requise pour ce cours.',
  },
  TEACHER_REVIEW: {
    label: 'À réviser par l\'enseignant',
    badge: 'bg-blue-100 text-blue-800 border-blue-300',
    criteria: '57 ≤ Note finale ≤ 59',
    explanation:
      'L\'élève est proche du seuil de passage. L\'enseignant peut exercer son jugement professionnel ' +
      'et réviser la note à la hausse. Si la note est maintenue, les crédits ne sont pas acquis.',
  },
  BORDERLINE: {
    label: 'Limite — candidat à l\'école d\'été',
    badge: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    criteria: '50 ≤ Note finale ≤ 56',
    explanation:
      'Les crédits ne sont pas acquis, mais la situation n\'est pas sans recours. ' +
      'L\'élève est typiquement admissible à l\'école d\'été pour récupérer les crédits manquants.',
  },
  CERTAIN_FAIL: {
    label: 'Échec certain',
    badge: 'bg-red-100 text-red-800 border-red-300',
    criteria: 'Note finale < 50',
    explanation:
      'Les crédits ne sont pas acquis et ne peuvent pas l\'être sans reprise complète du cours. ' +
      'L\'élève doit reprendre le cours l\'année suivante ou via l\'école d\'été (si admissible).',
  },
  NO_GRADE: {
    label: 'Sans note',
    badge: 'bg-gray-100 text-gray-600 border-gray-300',
    criteria: 'Note finale absente',
    explanation:
      'Aucune note finale n\'a été saisie pour cet élève dans ce cours. ' +
      'Les données sont incomplètes — à vérifier avec l\'enseignant responsable.',
  },
};

const GRADE_STYLE: Record<string, string> = {
  CERTAIN_PASS:   'text-green-700 font-bold',
  TEACHER_REVIEW: 'text-blue-700 font-bold',
  BORDERLINE:     'text-yellow-700 font-bold',
  CERTAIN_FAIL:   'text-red-700 font-bold',
  NO_GRADE:       'text-gray-400',
};

// ── Types ─────────────────────────────────────────────────────────────────────

interface CourseStudent {
  fiche: number;
  full_name: string;
  current_group: string;
  grade: number | null;
  classification: string;
  courses_below_60: number;
  courses_below_50: number;
  courses_below_60_list: string[];
  courses_below_50_list: string[];
  summer_school_enrollment_id: number | null;
  summer_school_course_code: string | null;
  summer_school_course_desc: string | null;
}

// ── Tooltip ───────────────────────────────────────────────────────────────────

function CountWithTooltip({ count, courses, activeClass }: {
  count: number;
  courses: string[];
  activeClass: string;
}) {
  if (count === 0) {
    return <span className="font-mono text-sm font-bold text-gray-300">—</span>;
  }
  return (
    <div className="relative group inline-block">
      <span className={`font-mono text-sm font-bold cursor-help underline decoration-dotted ${activeClass}`}>
        {count}
      </span>
      <div className="absolute right-0 bottom-full mb-2 w-72 bg-gray-900 text-white text-xs rounded-lg py-2 px-3 hidden group-hover:block z-50 shadow-xl pointer-events-none">
        <div className="text-gray-400 uppercase tracking-widest text-[9px] font-bold mb-1.5">
          {count} cours
        </div>
        {courses.map((c, i) => (
          <div key={i} className="py-0.5 border-t border-gray-700 first:border-0">{c}</div>
        ))}
        {/* Arrow */}
        <div className="absolute right-3 top-full w-2 h-2 bg-gray-900 rotate-45 -mt-1" />
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ClassificationDetail() {
  const { level, courseCode, classification } = useParams<{
    level: string;
    courseCode: string;
    classification: string;
  }>();

  const [allStudents, setAllStudents] = useState<CourseStudent[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState<number | null>(null);
  const year = '2025-2026';

  useEffect(() => {
    if (!level || !courseCode) return;
    client
      .get(`/students/projection/${level}/courses/${encodeURIComponent(courseCode)}/students`, {
        params: { year },
      })
      .then(res => setAllStudents(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [level, courseCode]);

  function handleEnroll(s: CourseStudent) {
    if (!courseCode) return;
    setEnrolling(s.fiche);
    client
      .post('/students/summer-school/enroll', {
        student_fiche: s.fiche,
        course_code: courseCode,
        academic_year: year,
      })
      .then(res => {
        setAllStudents(prev =>
          prev
            ? prev.map(st =>
                st.fiche === s.fiche
                  ? {
                      ...st,
                      summer_school_enrollment_id: res.data.id,
                      summer_school_course_code: res.data.course_code,
                      summer_school_course_desc: res.data.course_desc,
                    }
                  : st
              )
            : prev
        );
      })
      .catch(err => console.error(err))
      .finally(() => setEnrolling(null));
  }

  function handleCancel(s: CourseStudent) {
    if (!s.summer_school_enrollment_id) return;
    setEnrolling(s.fiche);
    client
      .delete(`/students/summer-school/${s.summer_school_enrollment_id}`)
      .then(() => {
        setAllStudents(prev =>
          prev
            ? prev.map(st =>
                st.fiche === s.fiche
                  ? {
                      ...st,
                      summer_school_enrollment_id: null,
                      summer_school_course_code: null,
                      summer_school_course_desc: null,
                    }
                  : st
              )
            : prev
        );
      })
      .catch(err => console.error(err))
      .finally(() => setEnrolling(null));
  }

  const cls = classification ?? 'ALL';
  const info = CLASS_INFO[cls] ?? CLASS_INFO['ALL'];

  const students =
    !allStudents ? [] :
    cls === 'ALL' ? allStudents :
    allStudents.filter(s => s.classification === cls);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">

      {/* Back */}
      <Link
        to="/stats"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        Retour à la projection
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-0.5">
              Sec {level} · {courseCode}
            </div>
            <h1 className="text-2xl font-black text-gray-900 uppercase tracking-tight">
              {courseCode}
            </h1>
          </div>
          <span className={`shrink-0 text-sm font-bold px-3 py-1.5 rounded-lg border ${info.badge}`}>
            {info.criteria}
          </span>
        </div>

        {/* Classification definition */}
        <div className="border-t border-gray-100 pt-3">
          <div className="text-base font-bold text-gray-800 mb-1">{info.label}</div>
          <p className="text-sm text-gray-600 leading-relaxed">{info.explanation}</p>
        </div>
      </div>

      {/* Student list */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-bold text-gray-800">
            {loading ? 'Chargement…' : `${students.length} élève${students.length !== 1 ? 's' : ''}`}
          </h2>
          {!loading && allStudents && cls !== 'ALL' && (
            <span className="text-xs text-gray-400">
              sur {allStudents.length} inscrits
            </span>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          </div>
        ) : students.length === 0 ? (
          <div className="px-6 py-10 text-center text-sm text-gray-400">
            Aucun élève dans cette catégorie.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 text-[10px] font-bold uppercase tracking-widest text-gray-400">
              <tr>
                <th className="px-6 py-3 text-left">Nom</th>
                <th className="px-6 py-3 text-left">Fiche</th>
                <th className="px-6 py-3 text-left">Groupe</th>
                <th className="px-6 py-3 text-right">Note ce cours</th>
                <th className="px-6 py-3 text-left pl-6">Statut</th>
                <th className="px-6 py-3 text-right" title="Cours avec note inférieure à 60 cette année">&lt; 60</th>
                <th className="px-6 py-3 text-right" title="Cours avec note inférieure à 50 cette année">&lt; 50</th>
                <th className="px-6 py-3 text-center">École d'été</th>
              </tr>
            </thead>
            <tbody>
              {students.map(s => {
                const isEnrolledHere = s.summer_school_course_code === courseCode;
                const isEnrolledElsewhere =
                  s.summer_school_enrollment_id !== null && !isEnrolledHere;
                const isBusy = enrolling === s.fiche;

                return (
                <tr key={s.fiche} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-6 py-3 text-sm font-medium text-gray-800">
                    <Link to={`/eleves/${s.fiche}`} className="hover:text-blue-600 hover:underline">
                      {s.full_name}
                    </Link>
                  </td>
                  <td className="px-6 py-3 font-mono text-xs text-gray-500">{s.fiche}</td>
                  <td className="px-6 py-3 font-mono text-xs text-gray-500">{s.current_group}</td>
                  <td className="px-6 py-3 text-right font-mono text-sm font-black">
                    {s.grade !== null ? s.grade : '—'}
                  </td>
                  <td className={`px-6 py-3 pl-6 text-xs font-semibold ${GRADE_STYLE[s.classification] ?? 'text-gray-500'}`}>
                    {s.classification.replace(/_/g, ' ')}
                  </td>
                  <td className="px-6 py-3 text-right">
                    <CountWithTooltip
                      count={s.courses_below_60}
                      courses={s.courses_below_60_list}
                      activeClass="text-yellow-600"
                    />
                  </td>
                  <td className="px-6 py-3 text-right">
                    <CountWithTooltip
                      count={s.courses_below_50}
                      courses={s.courses_below_50_list}
                      activeClass="text-red-600"
                    />
                  </td>
                  <td className="px-6 py-3 text-center">
                    {isEnrolledHere ? (
                      <button
                        onClick={() => handleCancel(s)}
                        disabled={isBusy}
                        title="Annuler l'inscription"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-orange-100 text-orange-700 border border-orange-300 hover:bg-orange-200 disabled:opacity-50 transition-colors"
                      >
                        {isBusy ? <Loader2 className="h-3 w-3 animate-spin" /> : <X className="h-3 w-3" />}
                        Inscrire ici
                      </button>
                    ) : isEnrolledElsewhere ? (
                      <span
                        title={`Déjà inscrit: ${s.summer_school_course_code} — ${s.summer_school_course_desc}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed"
                      >
                        <Sun className="h-3 w-3" />
                        {s.summer_school_course_code}
                      </span>
                    ) : (
                      <button
                        onClick={() => handleEnroll(s)}
                        disabled={isBusy}
                        title="Inscrire à l'école d'été pour ce cours"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-yellow-50 text-yellow-700 border border-yellow-300 hover:bg-yellow-100 disabled:opacity-50 transition-colors"
                      >
                        {isBusy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sun className="h-3 w-3" />}
                        Inscrire
                      </button>
                    )}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
