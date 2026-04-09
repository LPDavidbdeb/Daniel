import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  User, 
  ArrowLeft, 
  Loader2, 
  ChevronDown, 
  ChevronUp, 
  BookOpen, 
  Users,
  GraduationCap,
  CalendarDays
} from 'lucide-react';
import client from '@/api/client';

interface StudentMinimal {
  fiche: number;
  full_name: string;
}

interface Result {
  student: StudentMinimal;
  step_1_grade: number | null;
  step_2_grade: number | null;
  final_grade: number | null;
}

interface Offering {
  id: number;
  course_code: string;
  course_description: string;
  group_number: string;
  results: Result[];
}

interface Teacher {
  id: number;
  full_name: string;
  email: string;
  offerings: Offering[];
}

const getYearLabel = (firstDigit: string) => {
  const labels: Record<string, string> = {
    '1': '1re Secondaire',
    '2': '2e Secondaire',
    '3': '3e Secondaire',
    '4': '4e Secondaire',
    '5': '5e Secondaire',
  };
  return labels[firstDigit] || `Niveau ${firstDigit}`;
};

const TeacherDetail = () => {
  const { teacherId } = useParams();
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [loading, setLoading] = useState(true);
  const [openOfferings, setOpenOfferings] = useState<number[]>([]);

  useEffect(() => {
    client.get(`/school/${teacherId}`)
      .then(res => {
        setTeacher(res.data);
        if (res.data.offerings.length > 0) {
          setOpenOfferings([res.data.offerings[0].id]);
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [teacherId]);

  const toggleOffering = (id: number) => {
    setOpenOfferings(prev => 
      prev.includes(id) ? prev.filter(oid => oid !== id) : [...prev, id]
    );
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );

  if (!teacher) return <div className="p-6">Enseignant non trouvé.</div>;

  // Logique de groupement par année (1er chiffre du groupe)
  const groupedOfferings = teacher.offerings.reduce((acc, off) => {
    const year = off.group_number[0];
    if (!acc[year]) acc[year] = [];
    acc[year].push(off);
    return acc;
  }, {} as Record<string, Offering[]>);

  const sortedYears = Object.keys(groupedOfferings).sort();

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button onClick={() => window.history.back()} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <ArrowLeft className="h-6 w-6 text-gray-600" />
          </button>
          <h1 className="text-3xl font-black text-gray-900 uppercase tracking-tight">Dossier Enseignant</h1>
        </div>
      </div>

      {/* Header Card */}
      <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 flex flex-col md:flex-row gap-8 items-center">
        <div className="h-24 w-24 bg-indigo-50 rounded-2xl flex items-center justify-center border border-indigo-100 shadow-inner shrink-0">
          <User className="h-12 w-12 text-indigo-600" />
        </div>
        <div className="space-y-2 text-center md:text-left">
          <h2 className="text-3xl font-black text-gray-900 uppercase tracking-tight">{teacher.full_name}</h2>
          <p className="text-blue-600 font-mono font-medium">{teacher.email}</p>
          <div className="flex items-center justify-center md:justify-start gap-4 pt-2">
            <span className="flex items-center gap-1 text-xs font-bold text-gray-500 bg-gray-50 px-3 py-1 rounded-full border uppercase tracking-wider">
              <BookOpen className="h-4 w-4" /> {teacher.offerings.length} charges d'enseignement
            </span>
          </div>
        </div>
      </div>

      {/* Liste des charges groupées par année */}
      <div className="space-y-12">
        {sortedYears.map(year => (
          <div key={year} className="space-y-6">
            <div className="flex items-center gap-4 px-2">
              <div className="h-px flex-1 bg-gray-200"></div>
              <h3 className="flex items-center gap-2 text-sm font-black text-gray-400 uppercase tracking-[0.3em] whitespace-nowrap">
                <CalendarDays className="h-4 w-4" />
                {getYearLabel(year)}
              </h3>
              <div className="h-px flex-1 bg-gray-200"></div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {groupedOfferings[year].map((offering) => {
                const isOpen = openOfferings.includes(offering.id);
                return (
                  <div key={offering.id} className={`bg-white rounded-2xl border transition-all ${isOpen ? 'ring-4 ring-blue-500/5 border-blue-200' : 'border-gray-200 shadow-sm hover:border-gray-300'}`}>
                    <button 
                      onClick={() => toggleOffering(offering.id)}
                      className={`w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors rounded-2xl ${isOpen ? 'rounded-b-none border-b' : ''}`}
                    >
                      <div className="flex items-center gap-6">
                        <div className={`p-3 rounded-xl border font-black transition-colors ${isOpen ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-blue-600 border-gray-100 shadow-sm'}`}>
                          GRP {offering.group_number}
                        </div>
                        <div>
                          <p className="text-lg font-black text-gray-900 uppercase tracking-tight">{offering.course_description}</p>
                          <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest">Matière: {offering.course_code}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="hidden sm:flex flex-col items-end">
                          <span className="text-[10px] font-black text-gray-400 uppercase">Effectif</span>
                          <span className="text-sm font-bold text-gray-700">{offering.results.length} élèves</span>
                        </div>
                        {isOpen ? <ChevronUp className="h-6 w-6 text-gray-400" /> : <ChevronDown className="h-6 w-6 text-gray-400" />}
                      </div>
                    </button>

                    {isOpen && (
                      <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                        <table className="w-full text-left">
                          <thead className="bg-gray-50 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">
                            <tr>
                              <th className="px-8 py-4">Nom de l'élève</th>
                              <th className="px-8 py-4 text-center">Étape 1</th>
                              <th className="px-8 py-4 text-center">Étape 2</th>
                              <th className="px-8 py-4 text-center bg-blue-50/50">Som. Final</th>
                              <th className="px-8 py-4 text-right">Fiche</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {offering.results.map((res, idx) => (
                              <tr key={idx} className="hover:bg-blue-50/20 transition-colors group">
                                <td className="px-8 py-4">
                                  <p className="text-sm font-bold text-gray-900 uppercase group-hover:text-blue-600 transition-colors">
                                    {res.student.full_name}
                                  </p>
                                </td>
                                <td className="px-8 py-4 text-center text-sm font-bold text-gray-600">{res.step_1_grade ?? '-'}</td>
                                <td className="px-8 py-4 text-center text-sm font-bold text-gray-600">{res.step_2_grade ?? '-'}</td>
                                <td className={`px-8 py-4 text-center text-lg font-black bg-blue-50/10 ${res.final_grade && res.final_grade < 60 ? 'text-red-600' : 'text-blue-900'}`}>
                                  {res.final_grade ?? '-'}
                                </td>
                                <td className="px-8 py-4 text-right">
                                  <Link 
                                    to={`/eleves/${res.student.fiche}`}
                                    className="inline-flex items-center gap-1 text-[10px] font-black text-gray-400 hover:text-blue-600 transition-colors uppercase border border-gray-100 hover:border-blue-200 px-2 py-1 rounded-md"
                                  >
                                    <GraduationCap className="h-3 w-3" /> {res.student.fiche}
                                  </Link>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TeacherDetail;
