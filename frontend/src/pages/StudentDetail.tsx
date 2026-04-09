import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { User, ArrowLeft, Loader2, GraduationCap, TrendingUp, AlertCircle } from 'lucide-react';
import client from '@/api/client';

interface Result {
  course_code: string;
  course_description: string;
  teacher_name: string | null;
  teacher_id: number | null;
  step_1_grade: number | null;
  step_2_grade: number | null;
  final_grade: number | null;
}

interface Student {
  fiche: number;
  full_name: string;
  permanent_code: string;
  level: string;
  current_group: string;
  academic_profile: string;
  average: number | null;
  failed_courses_count: number;
  results: Result[];
}

const getProfileBadge = (profile: string) => {
  switch (profile) {
    case 'Fort':
    case 'Moyen-Fort':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'Fragile':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'À risque (1 échec)':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'En difficulté majeure':
      return 'bg-red-100 text-red-800 border-red-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const StudentDetail = () => {
  const { fiche } = useParams();
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get(`/students/${fiche}`)
      .then(res => setStudent(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [fiche]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );

  if (!student) return <div className="p-6 text-center text-gray-500 font-bold italic">Élève non trouvé.</div>;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex items-center space-x-4">
        <button onClick={() => window.history.back()} className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-600">
          <ArrowLeft className="h-6 w-6" />
        </button>
        <h1 className="text-3xl font-black text-gray-900 uppercase tracking-tight">Fiche Élève</h1>
      </div>

      {/* Profil Card */}
      <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-10 flex flex-col lg:flex-row gap-12">
        <div className="flex flex-col items-center space-y-4 shrink-0">
          <div className="h-32 w-32 bg-blue-50 rounded-3xl flex items-center justify-center border border-blue-100 shadow-inner">
            <User className="h-16 w-12 text-blue-600" />
          </div>
          <span className={`px-4 py-1.5 text-xs font-black rounded-full border shadow-sm uppercase tracking-widest ${getProfileBadge(student.academic_profile)}`}>
            {student.academic_profile}
          </span>
        </div>

        <div className="flex flex-col justify-between w-full space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-y-8 gap-x-12">
            <div>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">Identité</p>
              <p className="text-2xl font-black text-gray-900 uppercase">{student.full_name}</p>
            </div>
            <div>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">Fiche / Code permanent</p>
              <p className="text-lg font-bold text-gray-700">{student.fiche} / <span className="font-mono text-blue-600">{student.permanent_code}</span></p>
            </div>
            <div>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">Classe / Groupe</p>
              <p className="text-lg font-black text-gray-900">{student.level} / {student.current_group}</p>
            </div>
          </div>

          <div className="bg-gray-50/50 rounded-2xl p-6 border border-gray-100 grid grid-cols-1 sm:grid-cols-2 gap-8">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-white rounded-xl shadow-sm border border-gray-100">
                <TrendingUp className="h-6 w-6 text-indigo-600" />
              </div>
              <div>
                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Moyenne Générale</p>
                <p className="text-2xl font-black text-gray-900">{student.average !== null ? `${student.average}%` : 'N/A'}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`p-3 bg-white rounded-xl shadow-sm border ${student.failed_courses_count > 0 ? 'border-red-100' : 'border-gray-100'}`}>
                <AlertCircle className={`h-6 w-6 ${student.failed_courses_count > 0 ? 'text-red-600' : 'text-green-600'}`} />
              </div>
              <div>
                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Échecs (Som. Final)</p>
                <p className={`text-2xl font-black ${student.failed_courses_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {student.failed_courses_count}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Résultats */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2 px-2">
          <GraduationCap className="h-6 w-6 text-blue-600" />
          <h2 className="text-xl font-black text-gray-900 uppercase tracking-tight">Relevé de notes détaillé</h2>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b">
              <tr>
                <th className="px-8 py-5">Matière</th>
                <th className="px-8 py-5">Enseignant</th>
                <th className="px-8 py-5 text-center">Étape 1</th>
                <th className="px-8 py-5 text-center">Étape 2</th>
                <th className="px-8 py-5 text-center bg-blue-50/50">Note Finale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-medium">
              {student.results.map((result, idx) => (
                <tr key={idx} className="hover:bg-gray-50/50 transition-colors group">
                  <td className="px-8 py-5">
                    <p className="text-sm font-bold text-gray-900 uppercase">{result.course_description}</p>
                    <p className="text-xs text-gray-400 font-mono mt-0.5 uppercase tracking-tighter">Code: {result.course_code}</p>
                  </td>
                  <td className="px-8 py-5 text-sm">
                    {result.teacher_id ? (
                      <Link 
                        to={`/enseignants/${result.teacher_id}`}
                        className="text-blue-600 font-bold hover:text-blue-800 hover:underline decoration-2 underline-offset-4 transition-colors uppercase text-[10px] tracking-wider"
                      >
                        {result.teacher_name}
                      </Link>
                    ) : (
                      <span className="text-gray-400 italic text-xs uppercase">{result.teacher_name || 'Non assigné'}</span>
                    )}
                  </td>
                  <td className="px-8 py-5 text-center text-sm font-bold text-gray-700">{result.step_1_grade ?? '-'}</td>
                  <td className="px-8 py-5 text-center text-sm font-bold text-gray-700">{result.step_2_grade ?? '-'}</td>
                  <td className={`px-8 py-5 text-center text-lg font-black bg-blue-50/20 ${result.final_grade && result.final_grade < 60 ? 'text-red-600' : 'text-blue-900'}`}>
                    {result.final_grade ?? '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StudentDetail;
