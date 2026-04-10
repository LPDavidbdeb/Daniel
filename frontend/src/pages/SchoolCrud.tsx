import React, { useEffect, useState, useMemo } from 'react';
import { 
  BookOpen, 
  Users, 
  Presentation, 
  Plus, 
  Pencil, 
  Trash2, 
  Save, 
  X, 
  Loader2, 
  CheckCircle2,
  Search,
  Layers
} from 'lucide-react';
import * as api from '@/api/schoolCrud';

type Tab = 'courses' | 'teachers' | 'offerings' | 'cohorts';

const SchoolCrud = () => {
  const [activeTab, setActiveTab] = useState<Tab>('courses');
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Data
  const [courses, setCourses] = useState<api.Course[]>([]);
  const [teachers, setTeachers] = useState<api.Teacher[]>([]);
  const [offerings, setOfferings] = useState<api.CourseOffering[]>([]);
  const [cohorts, setCohorts] = useState<api.Cohort[]>([]);

  // Form State
  const [editingId, setEditingId] = useState<number | null>(null);
  const [courseForm, setCourseForm] = useState<api.SchoolCoursePayload>({
    local_code: '',
    meq_code: '',
    description: '',
    level: 1,
    credits: 0,
    periods: 0,
    is_core_or_sanctioned: false,
    is_active: true
  });

  const [cohortForm, setCohortForm] = useState<api.Cohort>({
    name: '',
    cohort_type: 'ZENITH',
    academic_year: '2025-2026',
    min_capacity: 15,
    max_capacity: 30,
    is_confirmed: false
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cRes, tRes, oRes, coRes] = await Promise.all([
        api.getCourses(),
        api.getTeachers(),
        api.getOfferings(),
        api.getCohorts().catch(() => [])
      ]);
      setCourses(cRes);
      setTeachers(tRes);
      setOfferings(oRes);
      setCohorts(coRes);
    } catch (err) {
      console.error("Erreur chargement:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // --- FILTRAGE ---
  const filteredCourses = useMemo(() => {
    return courses.filter(c => 
      c.local_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.meq_code && c.meq_code.includes(searchTerm))
    );
  }, [courses, searchTerm]);

  const filteredCohorts = useMemo(() => {
    return cohorts.filter(c => 
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.cohort_type.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [cohorts, searchTerm]);

  // --- ACTIONS ---
  const handleSaveCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) await api.updateCourse(editingId, courseForm);
      else await api.createCourse(courseForm);
      setEditingId(null);
      setCourseForm({ local_code: '', meq_code: '', description: '', level: 1, credits: 0, periods: 0, is_core_or_sanctioned: false, is_active: true });
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erreur d'enregistrement.");
    }
  };

  const handleEditCourse = (c: api.Course) => {
    setEditingId(c.id || null);
    setCourseForm({
      local_code: c.local_code,
      meq_code: c.meq_code,
      description: c.description,
      level: c.level,
      credits: c.credits,
      periods: c.periods,
      is_core_or_sanctioned: c.is_core_or_sanctioned,
      is_active: c.is_active,
    });
  };

  if (loading) return <div className="flex justify-center p-20"><Loader2 className="h-10 w-10 animate-spin text-blue-600" /></div>;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <h1 className="text-3xl font-black text-gray-900 uppercase tracking-tight">Configuration Scolaire</h1>
        
        <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
          {/* Barre de Recherche */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="Rechercher..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-bold focus:ring-4 focus:ring-blue-500/10 outline-none w-full sm:w-64 transition-all"
            />
          </div>

          <div className="flex bg-gray-100 p-1 rounded-xl shrink-0">
            {(['courses', 'teachers', 'offerings', 'cohorts'] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setActiveTab(t); setEditingId(null); setSearchTerm(''); }}
                className={`px-4 py-2 rounded-lg text-[10px] font-black uppercase transition-all ${activeTab === t ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                {t === 'courses' && "Cours"}
                {t === 'teachers' && "Profs"}
                {t === 'offerings' && "Groupes"}
                {t === 'cohorts' && "Cohortes"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* --- TAB COURSES --- */}
      {activeTab === 'courses' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm sticky top-24">
            <h2 className="text-lg font-black uppercase mb-6 flex items-center gap-2">
              {editingId ? <Pencil className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              {editingId ? "Modifier le cours" : "Ajouter un cours"}
            </h2>
            <form onSubmit={handleSaveCourse} className="space-y-4">
              <div>
                <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Code Local</label>
                <input required value={courseForm.local_code} onChange={e => setCourseForm({...courseForm, local_code: e.target.value.toUpperCase()})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold uppercase" />
              </div>
              <div>
                <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Code MEQ</label>
                <input value={courseForm.meq_code || ''} onChange={e => setCourseForm({...courseForm, meq_code: e.target.value})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Description</label>
                <input required value={courseForm.description} onChange={e => setCourseForm({...courseForm, description: e.target.value})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Niveau</label>
                  <input type="number" min="1" max="5" value={courseForm.level || ''} onChange={e => setCourseForm({...courseForm, level: parseInt(e.target.value)})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" />
                </div>
                <div>
                  <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Périodes</label>
                  <input type="number" min="0" value={courseForm.periods} onChange={e => setCourseForm({...courseForm, periods: parseInt(e.target.value)})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" />
                </div>
              </div>
              <div className="flex items-center gap-2 py-2">
                <input type="checkbox" id="is_core" checked={courseForm.is_core_or_sanctioned} onChange={e => setCourseForm({...courseForm, is_core_or_sanctioned: e.target.checked})} className="h-4 w-4 text-blue-600 rounded" />
                <label htmlFor="is_core" className="text-xs font-bold text-gray-700">Matière de base / Sanctionnée MEQ</label>
              </div>
              <div className="flex gap-2 pt-4">
                <button type="submit" className="flex-1 bg-blue-600 text-white font-black py-3 rounded-2xl text-xs uppercase hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20">
                  <Save className="h-3.5 w-3.5" /> Enregistrer
                </button>
                {editingId && (
                  <button type="button" onClick={() => setEditingId(null)} className="bg-gray-100 text-gray-500 p-3 rounded-2xl hover:bg-gray-200">
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white rounded-3xl border border-gray-200 shadow-sm overflow-hidden flex flex-col max-h-[calc(100vh-200px)]">
            <div className="overflow-auto">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-gray-50 z-10 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">Codes (L/M)</th>
                    <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">Description</th>
                    <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Niv/Pér</th>
                    <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Base</th>
                    <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredCourses.map(c => (
                    <tr key={c.id} className="hover:bg-blue-50/30 transition-colors">
                      <td className="px-6 py-4">
                        <p className="text-sm font-black text-gray-900">{c.local_code}</p>
                        <p className="text-[10px] font-mono font-bold text-blue-500">{c.meq_code || '-'}</p>
                      </td>
                      <td className="px-6 py-4 text-xs font-black text-gray-600 uppercase">{c.description}</td>
                      <td className="px-6 py-4 text-center">
                        <span className="text-xs font-black text-gray-900">S{c.level || '?'}</span>
                        <span className="mx-1 text-gray-300">|</span>
                        <span className="text-xs font-bold text-gray-500">{c.periods}p</span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        {c.is_core_or_sanctioned && <CheckCircle2 className="h-4 w-4 text-green-500 mx-auto" />}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-1">
                          <button onClick={() => handleEditCourse(c)} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"><Pencil className="h-4 w-4" /></button>
                          <button onClick={() => api.deleteCourse(c.id!).then(fetchData)} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"><Trash2 className="h-4 w-4" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {filteredCourses.length === 0 && (
                    <tr><td colSpan={5} className="p-20 text-center text-gray-400 text-xs font-black uppercase italic tracking-widest">Aucun cours trouvé</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB COHORTS --- */}
      {activeTab === 'cohorts' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm sticky top-24">
            <h2 className="text-lg font-black uppercase mb-6 flex items-center gap-2">Nouvelle Cohorte</h2>
            <form onSubmit={async (e) => { e.preventDefault(); await api.createCohort(cohortForm); fetchData(); }} className="space-y-4">
              <div>
                <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Nom de la cohorte</label>
                <input required value={cohortForm.name} onChange={e => setCohortForm({...cohortForm, name: e.target.value})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" placeholder="Ex: Zénith Sec 1" />
              </div>
              <div>
                <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Type</label>
                <select value={cohortForm.cohort_type} onChange={e => setCohortForm({...cohortForm, cohort_type: e.target.value as any})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold">
                  <option value="ZENITH">Zénith</option>
                  <option value="IFP">IFP</option>
                  <option value="DIM">DIM</option>
                  <option value="ACCUEIL">Accueil</option>
                  <option value="PARCOURS">Parcours</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Année</label>
                  <input required value={cohortForm.academic_year} onChange={e => setCohortForm({...cohortForm, academic_year: e.target.value})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" />
                </div>
                <div>
                  <label className="block text-[10px] font-black text-gray-400 uppercase mb-1">Capacité Min</label>
                  <input type="number" value={cohortForm.min_capacity} onChange={e => setCohortForm({...cohortForm, min_capacity: parseInt(e.target.value)})} className="w-full bg-gray-50 border rounded-xl px-4 py-2 text-sm font-bold" />
                </div>
              </div>
              <button type="submit" className="w-full bg-blue-600 text-white font-black py-4 rounded-2xl text-xs uppercase hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20">
                <Plus className="h-4 w-4" /> Créer la cohorte
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white rounded-3xl border border-gray-200 shadow-sm overflow-hidden flex flex-col max-h-[calc(100vh-200px)]">
            <div className="overflow-auto">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-gray-50 z-10 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">Nom</th>
                    <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">Type</th>
                    <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Année</th>
                    <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Capacité</th>
                    <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredCohorts.map(c => (
                    <tr key={c.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4 font-black text-gray-900 uppercase tracking-tight">{c.name}</td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 text-[9px] font-black rounded-md bg-indigo-50 text-indigo-600 border border-indigo-100 uppercase">{c.cohort_type}</span>
                      </td>
                      <td className="px-6 py-4 text-center text-xs font-bold text-gray-500">{c.academic_year}</td>
                      <td className="px-6 py-4 text-center text-xs font-bold text-gray-900">{c.min_capacity} él. min</td>
                      <td className="px-6 py-4 text-right">
                        <button onClick={() => api.deleteCohort(c.id!).then(fetchData)} className="p-2 text-gray-400 hover:text-red-600 rounded-xl transition-all"><Trash2 className="h-4 w-4" /></button>
                      </td>
                    </tr>
                  ))}
                  {filteredCohorts.length === 0 && (
                    <tr><td colSpan={5} className="p-20 text-center text-gray-400 text-xs font-black uppercase italic tracking-widest">Aucune cohorte trouvée</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB TEACHERS & OFFERINGS --- */}
      {activeTab === 'teachers' && (
        <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-20 text-center text-gray-400 text-xs font-black uppercase tracking-[0.2em] italic">
          Gestion des professeurs en lecture seule via l'importation GPI
        </div>
      )}
      
      {activeTab === 'offerings' && (
        <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-20 text-center text-gray-400 text-xs font-black uppercase tracking-[0.2em] italic">
          Les groupes-cours sont générés automatiquement lors de l'importation des résultats
        </div>
      )}
    </div>
  );
};

export default SchoolCrud;
