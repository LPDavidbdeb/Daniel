import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, ChevronRight, Loader2 } from 'lucide-react';
import client from '@/api/client';

interface Group {
  group_name: string;
  student_count: number;
}

const GroupList = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/students/groups')
      .then(res => setGroups(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Groupes d'élèves</h1>
        <p className="text-gray-500">Sélectionnez un groupe pour voir la liste des élèves.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group) => (
          <Link
            key={group.group_name}
            to={`/groupes/${encodeURIComponent(group.group_name)}`}
            className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-blue-400 transition-all group"
          >
            <div className="flex justify-between items-center">
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                  Groupe {group.group_name}
                </h3>
                <div className="flex items-center text-gray-500 text-sm">
                  <Users className="h-4 w-4 mr-1" />
                  <span>{group.student_count} élèves</span>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-gray-300 group-hover:text-blue-600 transition-colors" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default GroupList;
