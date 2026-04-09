import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Loader2, BookOpen, GraduationCap, ChevronRight } from 'lucide-react';
import client from '@/api/client';

interface Teacher {
  id: number;
  full_name: string;
  email: string;
  offerings: any[];
}

const TeacherList = () => {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/school/teachers')
      .then(res => setTeachers(res.data))
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
        <h1 className="text-3xl font-black text-gray-900 uppercase tracking-tight">Corps Enseignant</h1>
        <p className="text-gray-500 font-medium">Liste des professeurs et leurs charges d'enseignement.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {teachers.map((teacher) => (
          <Link
            key={teacher.id}
            to={`/enseignants/${teacher.id}`}
            className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:border-blue-400 transition-all group flex flex-col justify-between"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="h-12 w-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600 border border-blue-100">
                  <GraduationCap className="h-6 w-6" />
                </div>
                <ChevronRight className="h-5 w-5 text-gray-300 group-hover:text-blue-600 transition-colors" />
              </div>
              <div>
                <h3 className="text-lg font-black text-gray-900 uppercase tracking-tight group-hover:text-blue-600 transition-colors line-clamp-1">
                  {teacher.full_name}
                </h3>
                <p className="text-xs font-mono text-gray-400 truncate">{teacher.email}</p>
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between">
              <span className="flex items-center gap-1 text-xs font-bold text-gray-500 uppercase tracking-widest">
                <BookOpen className="h-3.5 w-3.5 text-gray-400" />
                {teacher.offerings.length} Cours
              </span>
              <span className="text-[10px] font-black text-blue-600 bg-blue-50 px-2 py-1 rounded-md uppercase">
                Consulter
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default TeacherList;
