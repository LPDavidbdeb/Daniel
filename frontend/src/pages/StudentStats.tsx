import React, { useEffect, useState } from 'react';
import { Users, Loader2, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, BookOpen } from 'lucide-react';
import client from '@/api/client';

interface CourseStat {
  code: string;
  description: string;
  count: number;
}

interface LevelStat {
  level: string;
  total_students: number;
  at_risk_count?: number; // Sec 1-2
  course_stats?: CourseStat[]; // Sec 3-5
}

const getLevelLabel = (level: string) => {
  const labels: Record<string, string> = {
    '1': '1re Secondaire',
    '2': '2e Secondaire',
    '3': '3e Secondaire',
    '4': '4e Secondaire',
    '5': '5e Secondaire',
  };
  return labels[level] || `Niveau ${level}`;
};

const StudentStats = () => {
  const [stats, setStats] = useState<LevelStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [openLevels, setOpenLevels] = useState<string[]>(['1', '2']); // Ouvert par défaut pour le 1er cycle

  useEffect(() => {
    client.get('/students/stats/summary')
      .then(res => setStats(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const toggleLevel = (level: string) => {
    setOpenLevels(prev => 
      prev.includes(level) ? prev.filter(l => l !== level) : [...prev, level]
    );
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-black text-gray-900 uppercase tracking-tight">Tableau de bord de Réussite</h1>
        <p className="text-gray-500 font-medium text-lg italic">
          Analyse du risque global (1er cycle) et par matière (2e cycle).
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {stats.map((lvl) => {
          const isOpen = openLevels.includes(lvl.level);
          const isFirstCycle = ['1', '2'].includes(lvl.level);

          return (
            <div key={lvl.level} className={`bg-white rounded-3xl border transition-all ${isOpen ? 'border-blue-200 shadow-xl ring-4 ring-blue-500/5' : 'border-gray-200 shadow-sm'}`}>
              <button 
                onClick={() => toggleLevel(lvl.level)}
                className="w-full flex items-center justify-between p-8 text-left"
              >
                <div className="flex items-center gap-6">
                  <div className={`h-16 w-16 rounded-2xl flex items-center justify-center font-black text-2xl border-2 transition-colors ${isOpen ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-100 text-blue-600 shadow-sm'}`}>
                    {lvl.level}
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-gray-900 uppercase tracking-tight">{getLevelLabel(lvl.level)}</h2>
                    <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                      {isFirstCycle ? "Indicateur de passage global" : "Réussite par matière"}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-12">
                  <div className="text-right">
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] block mb-1">Total Élèves</span>
                    <span className="text-2xl font-black text-gray-900">{lvl.total_students}</span>
                  </div>
                  {isFirstCycle && (
                    <div className="text-right bg-red-50 px-4 py-2 rounded-2xl border border-red-100">
                      <span className="text-[10px] font-black text-red-400 uppercase tracking-[0.2em] block mb-1">À risque (2+ échecs base)</span>
                      <span className="text-2xl font-black text-red-600">{lvl.at_risk_count}</span>
                    </div>
                  )}
                  {isOpen ? <ChevronUp className="h-6 w-6 text-gray-400" /> : <ChevronDown className="h-6 w-6 text-gray-400" />}
                </div>
              </button>

              {isOpen && (
                <div className="border-t border-gray-100 p-8 animate-in fade-in slide-in-from-top-2 duration-300">
                  {isFirstCycle ? (
                    <div className="bg-gray-50 rounded-2xl p-8 border border-gray-100 flex flex-col items-center text-center space-y-4">
                      <div className={`p-4 rounded-full ${lvl.at_risk_count === 0 ? 'bg-green-100' : 'bg-orange-100'}`}>
                        {lvl.at_risk_count === 0 ? <CheckCircle2 className="h-10 w-10 text-green-600" /> : <AlertCircle className="h-10 w-10 text-orange-600" />}
                      </div>
                      <div className="max-w-md">
                        <h3 className="text-xl font-black text-gray-900 uppercase mb-2">Analyse du passage au niveau suivant</h3>
                        <p className="text-gray-600 text-sm leading-relaxed font-medium">
                          Au 1er cycle, nous évaluons la progression sur les matières fondamentales (Français, Mathématiques, Anglais).
                          <br />
                          <strong>{lvl.at_risk_count} élèves</strong> présentent un échec sévère (moins de 50%) dans au moins deux de ces matières et doivent faire l'objet d'une révision.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="overflow-hidden rounded-2xl border border-gray-100 shadow-sm">
                      <table className="w-full text-left">
                        <thead className="bg-gray-50/50 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
                          <tr>
                            <th className="px-8 py-4">Cours</th>
                            <th className="px-8 py-4 text-right">Inscriptions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {lvl.course_stats?.map((c, i) => (
                            <tr key={i} className="hover:bg-blue-50/20 transition-colors">
                              <td className="px-8 py-4">
                                <div className="flex flex-col">
                                  <span className="text-sm font-black text-gray-800 uppercase tracking-tight">{c.description}</span>
                                  <span className="text-[10px] font-mono font-bold text-blue-500 uppercase">{c.code}</span>
                                </div>
                              </td>
                              <td className="px-8 py-4 text-right">
                                <span className="inline-flex items-center gap-2 bg-white px-4 py-1.5 rounded-full border border-gray-200 shadow-sm text-sm font-black text-gray-900">
                                  <Users className="h-3.5 w-3.5 text-blue-500" />
                                  {c.count}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StudentStats;
