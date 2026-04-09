import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Loader2, ArrowLeft, AlertTriangle } from 'lucide-react';
import client from '@/api/client';

interface Student {
  fiche: number;
  full_name: string;
  current_group: string;
  academic_profile: string;
  average: number | null;
  failed_courses_count: number;
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

const GroupDetail = () => {
  const { groupId } = useParams();
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get(`/students/groups/${groupId}/students`)
      .then(res => setStudents(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [groupId]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex items-center space-x-4">
        <Link to="/groupes" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <ArrowLeft className="h-6 w-6 text-gray-600" />
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 font-mono tracking-tight">GROUPE {groupId}</h1>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 text-xs font-bold text-gray-500 uppercase tracking-widest border-b border-gray-200">
            <tr>
              <th className="px-6 py-4">Fiche</th>
              <th className="px-6 py-4">Nom complet</th>
              <th className="px-6 py-4 text-center">Moyenne</th>
              <th className="px-6 py-4">Profil Académique</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {students.map((student) => (
              <tr key={student.fiche} className="hover:bg-blue-50/30 transition-colors">
                <td className="px-6 py-4 text-sm font-mono text-gray-500">{student.fiche}</td>
                <td className="px-6 py-4 text-sm text-gray-900 font-bold uppercase tracking-tight">{student.full_name}</td>
                <td className="px-6 py-4 text-sm text-center font-bold text-gray-700">
                  {student.average !== null ? `${student.average}%` : '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 text-xs font-bold rounded-full border shadow-sm inline-flex items-center gap-1 ${getProfileBadge(student.academic_profile)}`}>
                    {student.failed_courses_count > 0 && <AlertTriangle className="h-3 w-3" />}
                    {student.academic_profile}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <Link
                    to={`/eleves/${student.fiche}`}
                    className="inline-flex items-center space-x-1 text-sm font-black text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    <span>CONSULTER</span>
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default GroupDetail;
