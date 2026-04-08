import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Loader2, ArrowLeft, GraduationCap } from 'lucide-react';
import client from '@/api/client';

interface Student {
  fiche: number;
  full_name: string;
  current_group: string;
}

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
        <h1 className="text-3xl font-bold text-gray-900">Groupe {groupId}</h1>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4">Fiche</th>
              <th className="px-6 py-4">Nom complet</th>
              <th className="px-6 py-4">Profil</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {students.map((student) => (
              <tr key={student.fiche} className="hover:bg-blue-50/30 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{student.fiche}</td>
                <td className="px-6 py-4 text-sm text-gray-600 font-semibold">{student.full_name}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                    Non analysé
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <Link
                    to={`/eleves/${student.fiche}`}
                    className="inline-flex items-center space-x-1 text-sm font-bold text-blue-600 hover:text-blue-800"
                  >
                    <span>Profil</span>
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
