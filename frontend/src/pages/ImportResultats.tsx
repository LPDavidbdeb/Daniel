import React, { useState } from 'react';
import { Upload, AlertCircle, CheckCircle2, FileText, XCircle, Loader2, GraduationCap } from 'lucide-react';
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

    try {
      const response = await client.post('/ingestion/commit-results', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert(`Importation réussie !\n${response.data.count} résultats enregistrés.`);
      setFile(null);
      setReport(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erreur lors du commit.");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <GraduationCap className="h-8 w-8 text-blue-600" />
          Importation des Résultats
        </h1>
        <p className="text-gray-500">Analysez et synchronisez les notes des élèves depuis GPI.</p>
      </div>

      <div className="bg-white rounded-xl border-2 border-dashed border-gray-200 p-12 hover:border-blue-400 transition-all">
        <div className="flex flex-col items-center space-y-4">
          <div className="bg-blue-50 p-4 rounded-full">
            <Upload className="h-8 w-8 text-blue-600" />
          </div>
          <label className="cursor-pointer text-center">
            <span className="text-blue-600 font-bold hover:underline">Choisir l'extrait GPI</span>
            <span className="text-gray-500 ml-1">ou glisser-déposer</span>
            <input type="file" className="hidden" accept=".csv, .xlsx, .xls" onChange={handleFileChange} />
          </label>
          <p className="text-xs text-gray-400 mt-1">Formats acceptés : CSV, XLSX, XLS</p>
          {file && (
            <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1 rounded-full border border-gray-200">
              <FileText className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">{file.name}</span>
            </div>
          )}
          {file && !loading && !report && (
            <button onClick={handlePreview} className="mt-4 bg-blue-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-blue-700 shadow-md">
              Analyser le fichier
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center p-8 space-x-3 text-blue-600 animate-pulse">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce [animation-delay:0.2s]" />
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce [animation-delay:0.4s]" />
          <span className="font-medium italic">Analyse en cours...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
          <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-red-800">Erreur d'importation</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {report && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500">Total lignes</p>
              <p className="text-2xl font-bold">{report.total_lignes}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
              <p className="text-sm text-green-600">Lignes valides</p>
              <p className="text-2xl font-bold text-green-600">{report.lignes_valides}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
              <p className="text-sm text-red-600">Erreurs détectées</p>
              <p className="text-2xl font-bold text-red-600">{report.erreurs.length}</p>
            </div>
          </div>

          {report.erreurs.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <h3 className="font-bold text-gray-800">Détails des erreurs</h3>
              </div>
              <div className="overflow-x-auto max-h-[400px]">
                <table className="w-full text-left">
                  <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase sticky top-0">
                    <tr>
                      <th className="px-6 py-3">Ligne</th>
                      <th className="px-6 py-3">Élève / Matière</th>
                      <th className="px-6 py-3">Messages d'erreur</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {report.erreurs.map((err, idx) => (
                      <tr key={idx} className="hover:bg-red-50/20 transition-colors">
                        <td className="px-6 py-4 text-sm font-bold text-gray-900">{err.ligne}</td>
                        <td className="px-6 py-4 text-sm text-gray-600 font-medium">{err.identifiant}</td>
                        <td className="px-6 py-4 space-y-1">
                          {err.messages.map((msg, midx) => (
                            <div key={midx} className="flex items-center space-x-2 text-xs text-red-600 bg-red-50 px-2 py-1 rounded w-fit border border-red-100">
                              <AlertCircle className="h-3 w-3" />
                              <span>{msg}</span>
                            </div>
                          ))}
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
              className={`flex items-center space-x-2 px-10 py-3 rounded-lg font-bold shadow-md transition-all ${
                report.erreurs.length > 0 || report.total_lignes === 0 || committing
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700 transform hover:-translate-y-0.5'
              }`}
            >
              {committing ? <Loader2 className="h-5 w-5 animate-spin" /> : <CheckCircle2 className="h-5 w-5" />}
              <span>{committing ? 'Importation...' : "Confirmer l'importation"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportResultats;
