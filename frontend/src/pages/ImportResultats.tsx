import React, { useState } from 'react';
import { Upload, AlertCircle, CheckCircle2, FileText, XCircle, Loader2, GraduationCap, Calendar } from 'lucide-react';
import client from '@/api/client';

interface ValidationError {
  ligne: number;
  identifiant: string;
  messages: string[];
}

interface AnalysisReport {
  total_lignes: number;
  lignes_valides: number;
  erreurs: ValidationError[];
}

const ImportResultats = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [academicYear, setAcademicYear] = useState('2025-2026');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setReport(null);
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await client.post('/ingestion/preview-results', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur d'analyse.");
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!file) return;
    setCommitting(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('academic_year', academicYear);

    try {
      const response = await client.post('/ingestion/commit-results', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert(`Importation réussie pour ${academicYear} !\n${response.data.count} résultats enregistrés.`);
      setFile(null);
      setReport(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erreur lors du commit.");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 border-t-0">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <GraduationCap className="h-8 w-8 text-blue-600" />
          Importation des Résultats
        </h1>
        <p className="text-gray-500 font-medium">Synchronisez les notes des élèves pour une année scolaire spécifique.</p>
      </div>

      <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 flex flex-col md:flex-row gap-8 items-start">
        {/* Sélecteur d'année */}
        <div className="w-full md:w-1/3 space-y-4">
          <label className="flex items-center gap-2 text-xs font-black text-gray-400 uppercase tracking-widest px-1">
            <Calendar className="h-4 w-4" /> Année Scolaire
          </label>
          <select 
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 font-bold text-gray-900 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all"
          >
            <option value="2024-2025">2024-2025</option>
            <option value="2025-2026">2025-2026</option>
            <option value="2026-2027">2026-2027</option>
          </select>
        </div>

        {/* Zone de Drop */}
        <div className="w-full md:w-2/3">
          <div className="bg-blue-50/30 rounded-3xl border-2 border-dashed border-blue-200 p-8 hover:border-blue-400 transition-all flex flex-col items-center">
            <Upload className="h-10 w-10 text-blue-600 mb-4" />
            <label className="cursor-pointer text-center">
              <span className="text-blue-600 font-black hover:underline">Choisir l'extrait GPI</span>
              <input type="file" className="hidden" accept=".csv, .xlsx, .xls" onChange={handleFileChange} />
            </label>
            <p className="text-xs text-gray-400 font-bold uppercase mt-2">Formats: CSV, XLSX</p>
            
            {file && (
              <div className="mt-4 flex items-center gap-2 bg-white px-4 py-2 rounded-full border border-gray-100 shadow-sm">
                <FileText className="h-4 w-4 text-gray-400" />
                <span className="text-xs font-bold text-gray-700">{file.name}</span>
              </div>
            )}

            {file && !loading && !report && (
              <button onClick={handlePreview} className="mt-6 bg-blue-600 text-white px-10 py-2.5 rounded-xl font-black uppercase tracking-tighter hover:bg-blue-700 shadow-lg shadow-blue-600/20 transition-all">
                Analyser
              </button>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center p-8 space-x-3 text-blue-600 animate-pulse">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="font-black uppercase tracking-widest text-sm italic">Analyse du fichier...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 flex items-start gap-4">
          <XCircle className="h-6 w-6 text-red-600 shrink-0" />
          <div>
            <h3 className="text-sm font-black text-red-800 uppercase tracking-wider">Erreur d'importation</h3>
            <p className="text-sm text-red-700 mt-1 font-medium">{error}</p>
          </div>
        </div>
      )}

      {report && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Lignes</p>
              <p className="text-3xl font-black text-gray-900">{report.total_lignes}</p>
            </div>
            <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
              <p className="text-[10px] font-black text-green-400 uppercase tracking-widest mb-1">Prêtes</p>
              <p className="text-3xl font-black text-green-600">{report.lignes_valides}</p>
            </div>
            <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
              <p className="text-[10px] font-black text-red-400 uppercase tracking-widest mb-1">Erreurs</p>
              <p className="text-3xl font-black text-red-600">{report.erreurs.length}</p>
            </div>
          </div>

          {report.erreurs.length > 0 && (
            <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden shadow-sm">
              <div className="bg-gray-50 px-8 py-4 border-b">
                <h3 className="text-xs font-black text-gray-500 uppercase tracking-widest italic">Détail des anomalies détectées</h3>
              </div>
              <div className="overflow-x-auto max-h-[400px]">
                <table className="w-full text-left">
                  <thead className="bg-gray-50/50 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] border-b">
                    <tr>
                      <th className="px-8 py-4">Ligne</th>
                      <th className="px-8 py-4">Élève / Matière</th>
                      <th className="px-8 py-4">Messages</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 font-medium">
                    {report.erreurs.map((err, idx) => (
                      <tr key={idx} className="hover:bg-red-50/20 transition-colors">
                        <td className="px-8 py-4 font-black text-gray-900">{err.ligne}</td>
                        <td className="px-8 py-4 text-xs font-bold text-gray-600">{err.identifiant}</td>
                        <td className="px-8 py-4">
                          <div className="space-y-1">
                            {err.messages.map((msg, midx) => (
                              <div key={midx} className="flex items-center gap-2 text-[10px] font-bold text-red-600 bg-red-50 px-2 py-1 rounded-md border border-red-100 w-fit uppercase">
                                <AlertCircle className="h-3 w-3" /> {msg}
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex justify-end pt-4">
            <button
              disabled={report.erreurs.length > 0 || report.total_lignes === 0 || committing}
              onClick={handleCommit}
              className={`flex items-center gap-3 px-12 py-4 rounded-2xl font-black uppercase tracking-widest shadow-xl transition-all ${
                report.erreurs.length > 0 || report.total_lignes === 0 || committing
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none'
                  : 'bg-green-600 text-white hover:bg-green-700 hover:-translate-y-1 active:translate-y-0 shadow-green-600/20'
              }`}
            >
              {committing ? <Loader2 className="h-5 w-5 animate-spin" /> : <CheckCircle2 className="h-5 w-5" />}
              {committing ? 'Enregistrement...' : `Confirmer l'import ${academicYear}`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportResultats;
