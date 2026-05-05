import React, { useEffect, useState } from 'react';
import { Loader2, AlertCircle, CheckCircle, GraduationCap, ArrowRight, X, ChevronRight } from 'lucide-react';
import client from '@/api/client';
import { Link } from 'react-router-dom';

const LEVELS: { label: string; value: string }[] = [
  { label: 'Tous', value: '' },
  { label: 'Sec 1', value: '1' },
  { label: 'Sec 2', value: '2' },
  { label: 'Sec 3', value: '3' },
  { label: 'Sec 4', value: '4' },
  { label: 'Sec 5', value: '5' },
];

interface AcademicResult {
  course_code: string;
  course_description: string;
  course_group: string;
  teacher_name: string | null;
  step_1_grade: number | null;
  step_2_grade: number | null;
  final_grade: number | null;
}

interface StudentQueueItem {
  fiche: number;
  full_name: string;
  permanent_code: string;
  level: string;
  current_group: string;
  vetting_status: string;
  workflow_state: string;
  reason_codes: {
    message?: string;
    rule?: string;
    failed_courses?: string[];
    summer_eligible_courses?: string[];
    teacher_review_courses?: string[];
    micro_analysis?: {
      courses_evaluated: string[];
      state_distribution: Record<string, number>;
    };
  };
  results: AcademicResult[];
}

interface QueueDeskProps {
  title: string;
  endpoint: string;
  actionLabel: string;
  actionType: string;
  emptyMessage: string;
}

const QueueDesk: React.FC<QueueDeskProps> = ({
  title,
  endpoint,
  actionLabel,
  actionType,
  emptyMessage,
}) => {
  const [students, setStudents] = useState<StudentQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [selectedLevel, setSelectedLevel] = useState('');
  const [drawerStudent, setDrawerStudent] = useState<StudentQueueItem | null>(null);

  const fetchQueue = (levelValue: string) => {
    setLoading(true);
    const url = levelValue ? `${endpoint}?grade_level=${encodeURIComponent(levelValue)}` : endpoint;
    client.get(url)
      .then(res => setStudents(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue(selectedLevel);
  }, [endpoint, selectedLevel]);

  const handleLevelChange = (levelValue: string) => {
    setSelectedLevel(levelValue);
    setDrawerStudent(null);
  };

  const handleAction = (fiche: number) => {
    setProcessingId(fiche);
    client.post(`/students/${fiche}/evaluation`, {
      academic_year: '2025-2026',
      action: actionType,
      reason: `Action générée depuis le bureau ${title}`,
    })
      .then(() => {
        setStudents(prev => prev.filter(s => s.fiche !== fiche));
        if (drawerStudent?.fiche === fiche) setDrawerStudent(null);
      })
      .catch(err => {
        console.error(err);
        alert("Erreur lors de l'application de l'action.");
      })
      .finally(() => setProcessingId(null));
  };

  const gradeCls = (grade: number | null) => {
    if (grade === null) return 'text-gray-400';
    if (grade >= 60) return 'text-green-700 font-bold';
    if (grade >= 57) return 'text-orange-600 font-bold';
    if (grade >= 50) return 'text-yellow-600 font-bold';
    return 'text-red-600 font-bold';
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-end border-b-4 border-gray-900 pb-5">
        <div>
          <h1 className="text-5xl font-black text-gray-900 uppercase tracking-tighter leading-none">{title}</h1>
          <p className="mt-3 text-gray-500 font-medium text-lg italic">
            {loading ? '…' : `${students.length} dossier${students.length !== 1 ? 's' : ''} en attente`}
          </p>
        </div>
      </div>

      {/* Level tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 w-fit">
        {LEVELS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => handleLevelChange(value)}
            className={`px-4 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${
              selectedLevel === value
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* List + Drawer */}
      <div className="flex gap-6 items-start">
        {/* Student list */}
        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="flex flex-col items-center justify-center min-h-[300px] space-y-4">
              <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
              <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Chargement...</p>
            </div>
          ) : students.length === 0 ? (
            <div className="bg-green-50 rounded-3xl border-2 border-green-200 p-16 flex flex-col items-center text-center space-y-6">
              <CheckCircle className="h-16 w-16 text-green-600" />
              <div>
                <h2 className="text-2xl font-black text-green-900 uppercase tracking-tight">{emptyMessage}</h2>
                <p className="text-green-700 mt-2 font-medium italic">Tous les dossiers ont été traités.</p>
              </div>
              <Link to="/" className="text-green-800 font-black uppercase text-sm border-b-2 border-green-800 hover:text-green-900">
                Retour à l'accueil
              </Link>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border-2 border-gray-100 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-gray-100 bg-gray-50">
                    <th className="text-left px-5 py-3 text-[10px] font-black text-gray-400 uppercase tracking-widest">Élève</th>
                    <th className="text-left px-4 py-3 text-[10px] font-black text-gray-400 uppercase tracking-widest hidden md:table-cell">Groupe</th>
                    <th className="text-left px-4 py-3 text-[10px] font-black text-gray-400 uppercase tracking-widest hidden lg:table-cell">Niveau</th>
                    <th className="text-left px-4 py-3 text-[10px] font-black text-gray-400 uppercase tracking-widest">Diagnostic</th>
                    <th className="px-4 py-3 w-8"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {students.map(student => (
                    <tr
                      key={student.fiche}
                      onClick={() => setDrawerStudent(drawerStudent?.fiche === student.fiche ? null : student)}
                      className={`cursor-pointer transition-colors hover:bg-blue-50 ${
                        drawerStudent?.fiche === student.fiche ? 'bg-blue-50' : ''
                      }`}
                    >
                      <td className="px-5 py-3.5">
                        <div className="font-black text-gray-900 text-sm uppercase tracking-tight leading-tight">{student.full_name}</div>
                        <div className="text-[10px] font-mono text-blue-600 tracking-tighter">{student.permanent_code}</div>
                      </td>
                      <td className="px-4 py-3.5 hidden md:table-cell">
                        <span className="text-xs font-bold text-gray-500">{student.current_group}</span>
                      </td>
                      <td className="px-4 py-3.5 hidden lg:table-cell">
                        <span className="text-xs font-bold text-gray-500">{student.level}</span>
                      </td>
                      <td className="px-4 py-3.5 max-w-xs">
                        <p className="text-xs text-gray-600 truncate">{student.reason_codes.message || '—'}</p>
                      </td>
                      <td className="px-4 py-3.5">
                        <ChevronRight className={`h-4 w-4 text-gray-300 transition-transform ${
                          drawerStudent?.fiche === student.fiche ? 'rotate-90 text-blue-500' : ''
                        }`} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Drawer */}
        {drawerStudent && (
          <div className="w-full lg:w-[400px] shrink-0 bg-white rounded-2xl border-2 border-gray-200 shadow-xl overflow-hidden flex flex-col sticky top-6 max-h-[calc(100vh-48px)]">
            {/* Drawer header */}
            <div className="flex justify-between items-start p-5 border-b-2 border-gray-100">
              <div className="min-w-0 pr-2">
                <h2 className="text-base font-black text-gray-900 uppercase tracking-tight leading-tight truncate">{drawerStudent.full_name}</h2>
                <p className="text-[11px] font-mono text-blue-600 tracking-tighter mt-0.5">
                  {drawerStudent.permanent_code} · Fiche #{drawerStudent.fiche}
                </p>
              </div>
              <button
                onClick={() => setDrawerStudent(null)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-lg transition-colors shrink-0"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {/* Status badges */}
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 text-[10px] font-black rounded-full uppercase tracking-widest bg-orange-100 text-orange-800 border-2 border-orange-200">
                  {drawerStudent.vetting_status}
                </span>
                <span className="px-3 py-1 text-[10px] font-black rounded-full uppercase tracking-widest bg-blue-50 text-blue-700 border-2 border-blue-100">
                  {drawerStudent.workflow_state}
                </span>
                <span className="px-3 py-1 text-[10px] font-black rounded-full uppercase tracking-widest bg-gray-100 text-gray-600 border-2 border-gray-200">
                  {drawerStudent.level} · {drawerStudent.current_group}
                </span>
              </div>

              {/* Diagnostic */}
              <div className="bg-orange-50 rounded-xl p-4 space-y-3 border border-orange-100">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-orange-500 shrink-0" />
                  <span className="text-[10px] font-black text-orange-700 uppercase tracking-[0.2em]">Diagnostic</span>
                </div>
                <p className="text-sm font-medium text-gray-700 leading-relaxed">
                  {drawerStudent.reason_codes.message || 'Aucune justification.'}
                </p>
                {drawerStudent.reason_codes.rule && (
                  <span className="inline-block bg-orange-100 text-orange-800 text-[9px] font-black px-2 py-0.5 rounded border border-orange-200 uppercase tracking-widest">
                    {drawerStudent.reason_codes.rule}
                  </span>
                )}
                {(drawerStudent.reason_codes.failed_courses?.length ?? 0) > 0 && (
                  <div>
                    <p className="text-[10px] font-black text-red-600 uppercase tracking-widest mb-1">Échecs</p>
                    <div className="flex flex-wrap gap-1">
                      {drawerStudent.reason_codes.failed_courses!.map(c => (
                        <span key={c} className="bg-red-50 text-red-700 text-[9px] font-black px-2 py-0.5 rounded border border-red-100 uppercase">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
                {(drawerStudent.reason_codes.teacher_review_courses?.length ?? 0) > 0 && (
                  <div>
                    <p className="text-[10px] font-black text-orange-600 uppercase tracking-widest mb-1">Révision enseignant</p>
                    <div className="flex flex-wrap gap-1">
                      {drawerStudent.reason_codes.teacher_review_courses!.map(c => (
                        <span key={c} className="bg-orange-50 text-orange-700 text-[9px] font-black px-2 py-0.5 rounded border border-orange-100 uppercase">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
                {(drawerStudent.reason_codes.summer_eligible_courses?.length ?? 0) > 0 && (
                  <div>
                    <p className="text-[10px] font-black text-yellow-600 uppercase tracking-widest mb-1">École d'été</p>
                    <div className="flex flex-wrap gap-1">
                      {drawerStudent.reason_codes.summer_eligible_courses!.map(c => (
                        <span key={c} className="bg-yellow-50 text-yellow-700 text-[9px] font-black px-2 py-0.5 rounded border border-yellow-100 uppercase">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Grade history */}
              {drawerStudent.results.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Résultats</p>
                  <div className="rounded-xl overflow-hidden border border-gray-100">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                          <th className="text-left px-3 py-2 text-[9px] font-black text-gray-400 uppercase tracking-widest">Matière</th>
                          <th className="text-center px-2 py-2 text-[9px] font-black text-gray-400 uppercase tracking-widest">Ét.1</th>
                          <th className="text-center px-2 py-2 text-[9px] font-black text-gray-400 uppercase tracking-widest">Ét.2</th>
                          <th className="text-center px-2 py-2 text-[9px] font-black text-gray-400 uppercase tracking-widest">Final</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {drawerStudent.results.map(r => (
                          <tr key={r.course_code} className="bg-white">
                            <td className="px-3 py-2">
                              <div className="font-bold text-gray-700">{r.course_code}</div>
                              <div className="text-[9px] text-gray-400 truncate max-w-[110px]">{r.course_description}</div>
                            </td>
                            <td className={`text-center px-2 py-2 ${gradeCls(r.step_1_grade)}`}>{r.step_1_grade ?? '—'}</td>
                            <td className={`text-center px-2 py-2 ${gradeCls(r.step_2_grade)}`}>{r.step_2_grade ?? '—'}</td>
                            <td className={`text-center px-2 py-2 ${gradeCls(r.final_grade)}`}>{r.final_grade ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Drawer footer */}
            <div className="p-5 border-t-2 border-gray-100 space-y-3">
              <Link
                to={`/eleves/${drawerStudent.fiche}`}
                className="flex items-center justify-center gap-2 text-xs font-black text-gray-500 hover:text-gray-900 transition-colors uppercase tracking-widest"
              >
                <GraduationCap className="h-4 w-4" />
                <span>Voir le dossier complet</span>
              </Link>
              <button
                disabled={processingId === drawerStudent.fiche}
                onClick={() => handleAction(drawerStudent.fiche)}
                className={`w-full py-4 rounded-2xl font-black uppercase text-sm tracking-widest shadow-md transition-all flex items-center justify-center gap-3 ${
                  processingId === drawerStudent.fiche
                    ? 'bg-gray-300 text-white cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-[1.02] active:scale-100'
                }`}
              >
                {processingId === drawerStudent.fiche ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    <span>{actionLabel}</span>
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueueDesk;
