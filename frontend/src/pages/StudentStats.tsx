import { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, Loader2, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import client from '@/api/client';

// ── Types ────────────────────────────────────────────────────────────────────

interface LevelProjection {
  level: string;
  current_count: number;
  certain_promote: number;
  borderline: number;
  certain_retain: number;
  zenith_count: number;
  ifp_count: number;
  criteria_stub: boolean;
  target_size: number;
}

interface GroupProjection {
  group_name: string;
  stream: string;
  student_count: number;
  certain_promote: number;
  borderline: number;
  certain_retain: number;
  criteria_stub: boolean;
}

interface ClassifiedCourse {
  course_code: string;
  description: string;
  credits: number;
  grade: number | null;
  classification: string;
  is_sanctioned: boolean;
}

interface CourseProjection {
  course_code: string;
  description: string;
  credits: number;
  is_sanctioned: boolean;
  student_count: number;
  certain_pass: number;
  teacher_review: number;
  borderline: number;
  certain_fail: number;
  no_grade: number;
}

interface CourseStudent {
  fiche: number;
  full_name: string;
  current_group: string;
  grade: number | null;
  classification: string;
}

interface StudentProjection {
  fiche: number;
  full_name: string;
  current_group: string;
  promotion_outcome: string | null;
  review_reason: string | null;
  warnings: string[];
  criteria_stub: boolean;
  classified_courses: ClassifiedCourse[];
}

// ── Constants ────────────────────────────────────────────────────────────────

const LEVEL_LABEL: Record<string, string> = {
  '1': 'Sec 1', '2': 'Sec 2', '3': 'Sec 3', '4': 'Sec 4', '5': 'Sec 5',
};

const STREAM_LABEL: Record<string, string> = {
  REGULAR: 'Régulier', ZENITH: 'Zénith', IFP: 'IFP',
  ACCUEIL: 'Accueil', DIM: 'DIM', OTHER: 'Autre',
};

const STREAM_BADGE: Record<string, string> = {
  REGULAR: 'bg-gray-100 text-gray-700',
  ZENITH:  'bg-purple-100 text-purple-700',
  IFP:     'bg-orange-100 text-orange-700',
  ACCUEIL: 'bg-teal-100 text-teal-700',
  DIM:     'bg-yellow-100 text-yellow-700',
};

const OUTCOME_STYLE: Record<string, string> = {
  CERTAIN_PROMOTE: 'bg-green-50 text-green-700 border-green-200',
  BORDERLINE:      'bg-yellow-50 text-yellow-700 border-yellow-200',
  CERTAIN_RETAIN:  'bg-red-50 text-red-700 border-red-200',
};

const OUTCOME_LABEL: Record<string, string> = {
  CERTAIN_PROMOTE: 'Passe',
  BORDERLINE:      'À réviser',
  CERTAIN_RETAIN:  'Redouble',
};

const CLASS_STYLE: Record<string, string> = {
  CERTAIN_PASS:   'text-green-700 font-semibold',
  TEACHER_REVIEW: 'text-blue-700 font-semibold',
  BORDERLINE:     'text-yellow-700 font-semibold',
  CERTAIN_FAIL:   'text-red-700 font-semibold',
  NO_GRADE:       'text-gray-400',
};

// ── Small helpers ─────────────────────────────────────────────────────────────

function StubBadge() {
  return (
    <span title="Critères non confirmés" className="ml-1 inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-amber-600 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
      <AlertTriangle className="h-2.5 w-2.5" /> estimé
    </span>
  );
}

function groupCount(students: number, targetSize: number) {
  return Math.ceil(Math.max(0, students) / targetSize);
}

/** Formats a min–max range as "n" when equal, or "n–m" when they differ. */
function range(min: number, max: number): string {
  return min === max ? String(min) : `${min}–${max}`;
}

// ── Equation mini-card ────────────────────────────────────────────────────────

function EqCard({
  label,
  value,
  valueClass = 'text-gray-800',
  cardClass = 'bg-gray-50 border-gray-200',
  sub,
  to,
}: {
  label: string;
  value: React.ReactNode;
  valueClass?: string;
  cardClass?: string;
  sub?: string;
  to?: string;
}) {
  const inner = (
    <div className={`h-[52px] rounded-lg border px-2 flex flex-col items-center justify-center text-center gap-px ${cardClass} ${to ? 'cursor-pointer hover:brightness-95 transition-all' : ''}`}>
      <div className="text-[8px] font-bold uppercase tracking-wide text-gray-400 leading-tight">{label}</div>
      <div className={`text-sm font-black leading-none ${valueClass}`}>{value}</div>
      {sub && <div className="text-[8px] text-gray-400 leading-none">{sub}</div>}
    </div>
  );
  return to ? <Link to={to} className="contents">{inner}</Link> : inner;
}

// ── Student row ───────────────────────────────────────────────────────────────

function StudentRow({ student, isOpen, onToggle }: {
  student: StudentProjection;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const outcomeStyle = student.promotion_outcome ? OUTCOME_STYLE[student.promotion_outcome] ?? '' : '';
  const outcomeLabel = student.promotion_outcome ? OUTCOME_LABEL[student.promotion_outcome] ?? student.promotion_outcome : null;

  return (
    <>
      <tr
        className="hover:bg-gray-50 cursor-pointer border-b border-gray-100"
        onClick={onToggle}
      >
        <td className="px-4 py-2">
          {isOpen
            ? <ChevronDown className="h-3.5 w-3.5 text-gray-400 inline" />
            : <ChevronRight className="h-3.5 w-3.5 text-gray-400 inline" />}
        </td>
        <td className="px-4 py-2 font-mono text-xs text-gray-500">{student.fiche}</td>
        <td className="px-4 py-2 text-sm font-medium text-gray-800">{student.full_name}</td>
        <td className="px-4 py-2">
          {outcomeLabel && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded border ${outcomeStyle}`}>
              {outcomeLabel}
              {student.criteria_stub && <StubBadge />}
            </span>
          )}
        </td>
        <td className="px-4 py-2 text-xs text-gray-500 max-w-xs truncate">
          {student.review_reason}
          {student.warnings.map((w, i) => (
            <span key={i} className="ml-1 text-amber-600">⚠ {w}</span>
          ))}
        </td>
      </tr>
      {isOpen && (
        <tr className="bg-gray-50 border-b border-gray-100">
          <td colSpan={5} className="px-8 py-3">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 uppercase tracking-widest text-[10px]">
                  <th className="text-left pb-1">Cours</th>
                  <th className="text-right pb-1">Note</th>
                  <th className="text-right pb-1">Crédits</th>
                  <th className="text-left pb-1 pl-4">Statut</th>
                </tr>
              </thead>
              <tbody>
                {student.classified_courses.map((c) => (
                  <tr key={c.course_code} className="border-t border-gray-100">
                    <td className="py-0.5">
                      <span className="font-mono text-gray-500 mr-2">{c.course_code}</span>
                      {c.description}
                      {c.is_sanctioned && <span className="ml-1 text-[9px] text-blue-500 font-bold uppercase">base</span>}
                    </td>
                    <td className="text-right py-0.5 font-mono">
                      {c.grade !== null ? c.grade : '—'}
                    </td>
                    <td className="text-right py-0.5 font-mono">{c.credits}</td>
                    <td className={`pl-4 py-0.5 ${CLASS_STYLE[c.classification] ?? ''}`}>
                      {c.classification.replace('_', ' ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Group panel ───────────────────────────────────────────────────────────────

function GroupPanel({ level, group, targetSize, year }: {
  level: string;
  group: GroupProjection;
  targetSize: number;
  year: string;
}) {
  const [open, setOpen] = useState(false);
  const [students, setStudents] = useState<StudentProjection[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [openStudents, setOpenStudents] = useState<Set<number>>(new Set());

  const toggle = async () => {
    if (!open && students === null) {
      setLoading(true);
      const res = await client.get(`/students/projection/${level}/${encodeURIComponent(group.group_name)}/students`, { params: { year } });
      setStudents(res.data);
      setLoading(false);
    }
    setOpen(o => !o);
  };

  const toggleStudent = (fiche: number) =>
    setOpenStudents(prev => {
      const next = new Set(prev);
      next.has(fiche) ? next.delete(fiche) : next.add(fiche);
      return next;
    });

  const streamBadge = STREAM_BADGE[group.stream] ?? 'bg-gray-100 text-gray-700';
  const stub = group.criteria_stub;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center gap-4 px-4 py-3 bg-white hover:bg-gray-50 text-left"
      >
        {open ? <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />}

        {/* Group label */}
        <div className="shrink-0 w-16">
          <div className="font-mono font-bold text-gray-800 text-sm leading-tight">{group.group_name}</div>
          <div className="flex items-center gap-1 mt-0.5 flex-wrap">
            <span className={`text-[8px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded ${streamBadge}`}>
              {STREAM_LABEL[group.stream] ?? group.stream}
            </span>
            {stub && <StubBadge />}
          </div>
        </div>

        {/* Same 6-column grid as course panel */}
        <div className="flex-1 grid grid-cols-6 gap-2">
          <EqCard label="Élèves" value={group.student_count} />
          <EqCard
            label="Passe"
            value={stub ? '—' : group.certain_promote}
            valueClass={stub ? 'text-gray-300' : 'text-green-700'}
            cardClass={stub ? 'bg-gray-50 border-gray-100' : 'bg-green-50 border-green-100'}
          />
          <EqCard
            label="À réviser"
            value={stub ? '—' : group.borderline}
            valueClass={stub ? 'text-gray-300' : 'text-yellow-700'}
            cardClass={stub ? 'bg-gray-50 border-gray-100' : 'bg-yellow-50 border-yellow-100'}
          />
          <EqCard
            label="Redouble"
            value={stub ? '—' : group.certain_retain}
            valueClass={stub ? 'text-gray-300' : 'text-red-700'}
            cardClass={stub ? 'bg-gray-50 border-gray-100' : 'bg-red-50 border-red-100'}
          />
          <EqCard label="—" value="—" valueClass="text-gray-300" cardClass="bg-gray-50 border-gray-100" />
          <EqCard
            label="Groupes"
            value={groupCount(group.student_count, targetSize)}
            valueClass="text-blue-700"
            cardClass="bg-blue-50 border-blue-200"
            sub={`cible ${targetSize}`}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-gray-100">
          {loading ? (
            <div className="flex justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                <tr>
                  <th className="w-6 px-4 py-2" />
                  <th className="px-4 py-2 text-left">Fiche</th>
                  <th className="px-4 py-2 text-left">Nom</th>
                  <th className="px-4 py-2 text-left">Statut</th>
                  <th className="px-4 py-2 text-left">Détail</th>
                </tr>
              </thead>
              <tbody>
                {(students ?? []).map(s => (
                  <StudentRow
                    key={s.fiche}
                    student={s}
                    isOpen={openStudents.has(s.fiche)}
                    onToggle={() => toggleStudent(s.fiche)}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

// ── Course panel (Sec 3-4-5) ─────────────────────────────────────────────────

function CoursePanel({ level, course, targetSize, year }: {
  level: string;
  course: CourseProjection;
  targetSize: number;
  year: string;
}) {
  const [open, setOpen] = useState(false);
  const [students, setStudents] = useState<CourseStudent[] | null>(null);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    if (!open && students === null) {
      setLoading(true);
      const res = await client.get(
        `/students/projection/${level}/courses/${encodeURIComponent(course.course_code)}/students`,
        { params: { year } },
      );
      setStudents(res.data);
      setLoading(false);
    }
    setOpen(o => !o);
  };

  const groups = groupCount(course.student_count, targetSize);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="w-full flex items-center gap-4 px-4 py-3 bg-white hover:bg-gray-50">

        {/* Left side: chevron + label — clicking here toggles the accordion */}
        <div
          onClick={toggle}
          className="flex items-center gap-3 shrink-0 cursor-pointer"
        >
          {open
            ? <ChevronDown className="h-4 w-4 text-gray-400" />
            : <ChevronRight className="h-4 w-4 text-gray-400" />}
          <div className="w-16">
            <div className="font-mono text-[10px] text-gray-400 leading-tight">{course.course_code}</div>
            <div className="text-xs font-semibold text-gray-800 leading-tight line-clamp-2">{course.description}</div>
            {course.is_sanctioned && (
              <span className="text-[8px] text-blue-500 font-bold uppercase">base</span>
            )}
          </div>
        </div>

        {/* Cards — each is a Link, no button wrapper */}
        <div className="flex-1 grid grid-cols-6 gap-2">
          <EqCard label="Inscrits"  value={course.student_count} to={`/stats/cours/${level}/${encodeURIComponent(course.course_code)}/ALL`} />
          <EqCard label="Passe"     value={course.certain_pass}   valueClass="text-green-700"  cardClass="bg-green-50 border-green-100"   to={`/stats/cours/${level}/${encodeURIComponent(course.course_code)}/CERTAIN_PASS`} />
          <EqCard label="À réviser" value={course.teacher_review} valueClass="text-blue-700"   cardClass="bg-blue-50 border-blue-100"    to={`/stats/cours/${level}/${encodeURIComponent(course.course_code)}/TEACHER_REVIEW`} />
          <EqCard label="Limite"    value={course.borderline}     valueClass="text-yellow-700" cardClass="bg-yellow-50 border-yellow-100" to={`/stats/cours/${level}/${encodeURIComponent(course.course_code)}/BORDERLINE`} />
          <EqCard label="Échoue"    value={course.certain_fail}   valueClass="text-red-700"    cardClass="bg-red-50 border-red-100"      to={`/stats/cours/${level}/${encodeURIComponent(course.course_code)}/CERTAIN_FAIL`} />
          <EqCard label="Groupes"   value={groups}                valueClass="text-blue-700"   cardClass="bg-blue-50 border-blue-200"    sub={`cible ${targetSize}`} />
        </div>
      </div>

      {open && (
        <div className="border-t border-gray-100">
          {loading ? (
            <div className="flex justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                <tr>
                  <th className="px-4 py-2 text-left">Fiche</th>
                  <th className="px-4 py-2 text-left">Nom</th>
                  <th className="px-4 py-2 text-left">Groupe</th>
                  <th className="px-4 py-2 text-right">Note</th>
                  <th className="px-4 py-2 text-left pl-4">Statut</th>
                </tr>
              </thead>
              <tbody>
                {(students ?? []).map(s => (
                  <tr key={s.fiche} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs text-gray-500">{s.fiche}</td>
                    <td className="px-4 py-2 text-sm text-gray-800">{s.full_name}</td>
                    <td className="px-4 py-2 font-mono text-xs text-gray-500">{s.current_group}</td>
                    <td className="px-4 py-2 text-right font-mono text-sm font-bold">
                      {s.grade !== null ? s.grade : '—'}
                    </td>
                    <td className={`px-4 py-2 pl-4 text-xs ${CLASS_STYLE[s.classification] ?? ''}`}>
                      {s.classification.replace(/_/g, ' ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

// ── Level panel ───────────────────────────────────────────────────────────────

function LevelPanel({ level, projection, allLevels, levelIndex, year }: {
  level: string;
  projection: LevelProjection;
  allLevels: LevelProjection[];
  levelIndex: number;
  year: string;
}) {
  const [open, setOpen] = useState(false);
  const [groups, setGroups] = useState<GroupProjection[] | null>(null);
  const [courses, setCourses] = useState<CourseProjection[] | null>(null);
  const [loading, setLoading] = useState(false);

  const prev = levelIndex > 0 ? allLevels[levelIndex - 1] : null;
  const cur = projection;

  // Content is based on the SOURCE level (prev), not the target level.
  // prev.level 1-2 → closed/global rules → show groups
  // prev.level 3-4 → open/per-course rules → show courses
  // no prev (Sec 1) → nothing to show (primary school data missing)
  const isOpen = prev !== null && parseInt(prev.level) >= 3;

  const toggle = async () => {
    if (!open && prev) {
      if (isOpen && courses === null) {
        setLoading(true);
        const res = await client.get(`/students/projection/${prev.level}/courses`, { params: { year } });
        setCourses(res.data);
        setLoading(false);
      } else if (!isOpen && groups === null) {
        setLoading(true);
        const res = await client.get(`/students/projection/${prev.level}/groups`, { params: { year } });
        setGroups(res.data);
        setLoading(false);
      }
    }
    setOpen(o => !o);
  };

  // ── Projection math ──────────────────────────────────────────────────────
  // students_next[N] = current[N-1] − holdbacks[N-1] + holdbacks[N]
  // Zénith and IFP are drawn from prev level (the ones advancing)

  const hasProjection = prev !== null;

  // Holdbacks from N-1 (range: certain_retain is guaranteed; +borderline is worst case)
  const holdbackPrevMin = prev ? prev.certain_retain : 0;
  const holdbackPrevMax = prev ? prev.certain_retain + prev.borderline : 0;

  // Holdbacks staying at N (range: certain_retain is guaranteed; +borderline is worst case)
  const holdbackCurMin = cur.certain_retain;
  const holdbackCurMax = cur.certain_retain + cur.borderline;

  // Advancing Zénith / IFP from N-1 (approximation: all current N-1 Zénith/IFP advance)
  const zenithAdvancing = prev ? prev.zenith_count : 0;
  const ifpAdvancing    = prev ? prev.ifp_count    : 0;

  // Total students arriving at level N next year
  const minTotal = hasProjection
    ? Math.max(0, (prev!.current_count - holdbackPrevMax) + holdbackCurMin)
    : null;
  const maxTotal = hasProjection
    ? Math.max(0, (prev!.current_count - holdbackPrevMin) + holdbackCurMax)
    : null;

  // Regular students only (total minus special streams)
  const minRegular = minTotal !== null ? Math.max(0, minTotal - zenithAdvancing - ifpAdvancing) : null;
  const maxRegular = maxTotal !== null ? Math.max(0, maxTotal - zenithAdvancing - ifpAdvancing) : null;

  const minGroups = minRegular !== null ? groupCount(minRegular, cur.target_size) : null;
  const maxGroups = maxRegular !== null ? groupCount(maxRegular, cur.target_size) : null;

  const stub = cur.criteria_stub || (prev?.criteria_stub ?? false);

  return (
    <div className={`rounded-xl border bg-white transition-all ${open ? 'border-blue-200 shadow-md' : 'border-gray-200'}`}>
      <button onClick={toggle} className="w-full flex items-center gap-4 px-5 py-4 text-left">

        {/* Chevron */}
        {open
          ? <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" />
          : <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />}

        {/* Level badge */}
        <div className={`h-9 w-9 shrink-0 rounded-lg flex items-center justify-center font-black text-base border-2 ${open ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-200 text-blue-600'}`}>
          {level}
        </div>

        {/* Label */}
        <div className="shrink-0 w-16">
          <div className="font-black text-gray-900 uppercase tracking-tight leading-tight">{LEVEL_LABEL[level]}</div>
          <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-widest">
            {!prev ? '—' : isOpen ? 'Ouvert' : 'Fermé'}
          </div>
        </div>

        {/* ── 6-column grid, always full width, always all columns ── */}
        <div className="flex-1 grid grid-cols-6 gap-2">

          {/* Col 1 — students from level N-1 */}
          <EqCard
            label={prev ? `Sec ${prev.level}` : 'Sec N-1'}
            value={prev ? prev.current_count : '—'}
            valueClass={prev ? 'text-gray-800' : 'text-gray-300'}
            cardClass={prev ? 'bg-gray-50 border-gray-200' : 'bg-gray-50 border-gray-100'}
          />

          {/* Col 2 — holdbacks staying at N-1 */}
          <EqCard
            label="Redoub. N-1"
            value={prev ? range(holdbackPrevMin, holdbackPrevMax) : '—'}
            valueClass={prev ? 'text-red-700' : 'text-gray-300'}
            cardClass={prev ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-gray-100'}
          />

          {/* Col 3 — holdbacks repeating level N */}
          <EqCard
            label="Redoub. N"
            value={range(holdbackCurMin, holdbackCurMax)}
            valueClass="text-green-700"
            cardClass="bg-green-50 border-green-100"
          />

          {/* Col 4 — Zénith advancing from N-1 */}
          <EqCard
            label="Zénith ↗"
            value={prev ? zenithAdvancing : '—'}
            valueClass={zenithAdvancing > 0 ? 'text-purple-700' : 'text-gray-300'}
            cardClass={zenithAdvancing > 0 ? 'bg-purple-50 border-purple-100' : 'bg-gray-50 border-gray-100'}
            sub={zenithAdvancing > 0 ? `${groupCount(zenithAdvancing, cur.target_size)} gr.` : undefined}
          />

          {/* Col 5 — IFP advancing from N-1 */}
          <EqCard
            label="IFP ↗"
            value={prev ? ifpAdvancing : '—'}
            valueClass={ifpAdvancing > 0 ? 'text-orange-700' : 'text-gray-300'}
            cardClass={ifpAdvancing > 0 ? 'bg-orange-50 border-orange-100' : 'bg-gray-50 border-gray-100'}
            sub={ifpAdvancing > 0 ? `${groupCount(ifpAdvancing, cur.target_size)} gr.` : undefined}
          />

          {/* Col 6 — result */}
          <EqCard
            label="Groupes"
            value={
              hasProjection && minGroups !== null && maxGroups !== null
                ? <>{range(minGroups, maxGroups)}{stub && <span className="text-[10px] font-normal"> ~</span>}</>
                : '—'
            }
            valueClass={hasProjection ? 'text-blue-700' : 'text-gray-300'}
            cardClass={hasProjection ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-100'}
            sub={hasProjection ? `cible ${cur.target_size}` : undefined}
          />

        </div>
      </button>

      {open && (
        <div className="border-t border-gray-100 px-5 pb-5 pt-3 space-y-3">
          {!prev ? (
            <p className="text-sm text-gray-400 italic py-4 text-center">
              Données manquantes : inscriptions des écoles primaires requises.
            </p>
          ) : loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : isOpen ? (
            (courses ?? []).map(c => (
              <CoursePanel key={c.course_code} level={prev.level} course={c} targetSize={cur.target_size} year={year} />
            ))
          ) : (
            (groups ?? []).map(g => (
              <GroupPanel key={g.group_name} level={prev.level} group={g} targetSize={cur.target_size} year={year} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function StudentStats() {
  const [levels, setLevels] = useState<LevelProjection[]>([]);
  const [loading, setLoading] = useState(true);
  const year = '2025-2026';

  useEffect(() => {
    client.get('/students/projection/summary', { params: { year } })
      .then(res => setLevels(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [year]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <p className="text-sm text-gray-500">Calcul des projections en cours…</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-black text-gray-900 uppercase tracking-tight">Projection des groupes</h1>
        <p className="text-gray-500 mt-1">
          Estimation du nombre de groupes réguliers l'année prochaine.
          Les colonnes Zénith ↗ et IFP ↗ indiquent les élèves qui avancent — à vous de juger si le nombre justifie un groupe à part.
        </p>
      </div>

      <div className="space-y-3">
        {levels.map((lvl, i) => (
          <LevelPanel
            key={lvl.level}
            level={lvl.level}
            projection={lvl}
            allLevels={levels}
            levelIndex={i}
            year={year}
          />
        ))}
      </div>
    </div>
  );
}
