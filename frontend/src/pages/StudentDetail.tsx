import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { User, ArrowLeft, Loader2, GraduationCap } from 'lucide-react';
import client from '@/api/client';

interface Result {
  course_code: string;
  course_description: string;
  teacher_name: string;
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
  results: Result[];
}

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

  if (!student) return <div className="p-6">Élève non trouvé.</div>;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex items-center space-x-4">
        <button onClick={() => window.history.back()} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <ArrowLeft className="h-6 w-6 text-gray-600" />
        </button>
        <h1 className="text-3xl font-bold text-gray-900 uppercase">Fiche Élève</h1>
      </div>

      {/* Profil Card */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 flex flex-col md:flex-row gap-8">
        <div className="h-24 w-24 bg-blue-50 rounded-2xl flex items-center justify-center shrink-0 border border-blue-100">
          <User className="h-12 w-12 text-blue-600" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-y-6 gap-x-12 w-full">
          <div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Nom complet</p>
            <p className="text-xl font-bold text-gray-900">{student.full_name}</p>
          </div>
          <div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Fiche / Code permanent</p>
            <p className="text-gray-700 font-semibold">{student.fiche} / <span className="font-mono text-sm">{student.permanent_code}</span></p>
          </div>
          <div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Groupe / Classe</p>
            <p className="text-gray-700 font-bold">{student.current_group} / {student.level}</p>
          </div>
        </div>
      </div>

      {/* Résultats */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <GraduationCap className="h-6 w-6 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900">Résultats scolaires</h2>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b">
              <tr>
                <th className="px-6 py-4">Matière</th>
                <th className="px-6 py-4">Enseignant</th>
                <th className="px-6 py-4 text-center">Étape 1</th>
                <th className="px-6 py-4 text-center">Étape 2</th>
                <th className="px-6 py-4 text-center bg-blue-50/50">Som. Final</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {student.results.map((result, idx) => (
                <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <p className="text-sm font-bold text-gray-900 uppercase">{result.course_description}</p>
                    <p className="text-xs text-gray-400 font-mono">{result.course_code}</p>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{result.teacher_name || '-'}</td>
                  <td className="px-6 py-4 text-center text-sm font-medium">{result.step_1_grade ?? '-'}</td>
                  <td className="px-6 py-4 text-center text-sm font-medium">{result.step_2_grade ?? '-'}</td>
                  <td className={`px-6 py-4 text-center font-bold bg-blue-50/30 ${result.final_grade && result.final_grade < 60 ? 'text-red-600' : 'text-gray-900'}`}>
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
