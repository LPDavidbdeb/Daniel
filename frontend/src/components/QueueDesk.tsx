import React, { useEffect, useState } from 'react';
import { Loader2, AlertCircle, CheckCircle, GraduationCap, ArrowRight, User } from 'lucide-react';
import client from '@/api/client';
import { Link } from 'react-router-dom';

interface StudentQueueItem {
  fiche: number;
  full_name: string;
  permanent_code: string;
  level: string;
  current_group: string;
  vetting_status: string;
  workflow_state: string;
  reason_codes: {
    message?: string;
    failures?: string[];
    action?: string;
    reason?: string;
  };
}

interface QueueDeskProps {
  title: string;
  endpoint: string;
  actionLabel: string;
  actionType: string;
  emptyMessage: string;
}

const QueueDesk: React.FC<QueueDeskProps> = ({ 
  title, 
  endpoint, 
  actionLabel, 
  actionType,
  emptyMessage 
}) => {
  const [students, setStudents] = useState<StudentQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<number | null>(null);

  const fetchQueue = () => {
    setLoading(true);
    client.get(endpoint)
      .then(res => setStudents(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, [endpoint]);

  const handleAction = (fiche: number) => {
    setProcessingId(fiche);
    
    // US4.3 Hook: Simulate or call US3.3 bridge
    // Here we use a generic evaluation action that resolves the review
    const payload = {
      academic_year: "2025-2026",
      action: actionType, // e.g., 'RESOLVE_REVIEW'
      reason: `Action auto-générée depuis le bureau ${title}`,
    };

    client.post(`/students/${fiche}/evaluation`, payload)
      .then(() => {
        // Optimistic UI update: Remove student from list immediately
        setStudents(prev => prev.filter(s => s.fiche !== fiche));
      })
      .catch(err => {
        console.error(err);
        alert("Erreur lors de l'application de l'action.");
      })
      .finally(() => setProcessingId(null));
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Chargement du bureau...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <div className="flex justify-between items-end border-b-4 border-gray-900 pb-6">
        <div>
          <h1 className="text-5xl font-black text-gray-900 uppercase tracking-tighter leading-none">{title}</h1>
          <p className="mt-4 text-gray-500 font-medium text-lg italic">
            {students.length} dossier{students.length > 1 ? 's' : ''} en attente d'action.
          </p>
        </div>
      </div>

      {students.length === 0 ? (
        <div className="bg-green-50 rounded-3xl border-2 border-green-200 p-16 flex flex-col items-center text-center space-y-6">
          <div className="bg-green-100 p-6 rounded-full shadow-inner">
            <CheckCircle className="h-16 w-16 text-green-600" />
          </div>
          <div>
            <h2 className="text-3xl font-black text-green-900 uppercase tracking-tight">{emptyMessage}</h2>
            <p className="text-green-700 mt-2 font-medium italic">Tous les dossiers ont été traités avec succès.</p>
          </div>
          <Link to="/" className="text-green-800 font-black uppercase text-sm border-b-2 border-green-800 hover:text-green-900">
            Retour à l'accueil
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {students.map(student => (
            <div key={student.fiche} className="bg-white rounded-3xl border-2 border-gray-100 shadow-xl hover:shadow-2xl transition-all overflow-hidden flex flex-col group">
              <div className="p-8 space-y-6 flex-grow">
                {/* Header */}
                <div className="flex justify-between items-start">
                  <div className="h-16 w-16 bg-gray-50 rounded-2xl flex items-center justify-center border-2 border-gray-100 group-hover:bg-blue-50 group-hover:border-blue-100 transition-colors">
                    <User className="h-8 w-8 text-gray-400 group-hover:text-blue-500 transition-colors" />
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-xs font-black text-gray-400 uppercase tracking-widest">{student.current_group}</span>
                    <span className="text-[10px] font-bold text-blue-600 font-mono tracking-tighter">{student.permanent_code}</span>
                  </div>
                </div>

                {/* Identity */}
                <div>
                  <h3 className="text-2xl font-black text-gray-900 uppercase tracking-tight leading-tight group-hover:text-blue-600 transition-colors">
                    {student.full_name}
                  </h3>
                  <p className="text-sm font-bold text-gray-400 italic">Fiche #{student.fiche}</p>
                </div>

                {/* Status Badges */}
                <div className="flex flex-wrap gap-2">
                  <span className={`px-3 py-1 text-[10px] font-black rounded-full uppercase tracking-widest shadow-sm ${
                    student.vetting_status === 'REQUIRES_REVIEW' 
                      ? 'bg-orange-100 text-orange-800 border-2 border-orange-200' 
                      : 'bg-green-100 text-green-800 border-2 border-green-200'
                  }`}>
                    {student.vetting_status}
                  </span>
                  <span className="px-3 py-1 text-[10px] font-black rounded-full uppercase tracking-widest bg-blue-50 text-blue-700 border-2 border-blue-100">
                    {student.workflow_state}
                  </span>
                </div>

                {/* Diagnosis / Why */}
                <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 space-y-3">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="h-4 w-4 text-orange-500" />
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Diagnostic</p>
                  </div>
                  <p className="text-sm font-bold text-gray-700 italic leading-relaxed">
                    {student.reason_codes.message || "Aucune justification détaillée."}
                  </p>
                  {student.reason_codes.failures && student.reason_codes.failures.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {student.reason_codes.failures.map(code => (
                        <span key={code} className="bg-red-50 text-red-700 text-[9px] font-black px-2 py-0.5 rounded border border-red-100 uppercase">
                          {code}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Actions Footer */}
              <div className="bg-gray-50 border-t-2 border-gray-100 p-6 flex flex-col space-y-4">
                <Link 
                  to={`/eleves/${student.fiche}`}
                  className="flex items-center justify-center space-x-2 text-xs font-black text-gray-500 hover:text-gray-900 transition-colors uppercase tracking-widest"
                >
                  <GraduationCap className="h-4 w-4" />
                  <span>Consulter le dossier</span>
                </Link>
                <button
                  disabled={processingId === student.fiche}
                  onClick={() => handleAction(student.fiche)}
                  className={`w-full py-4 rounded-2xl font-black uppercase text-sm tracking-widest shadow-md transition-all flex items-center justify-center space-x-3 ${
                    processingId === student.fiche 
                      ? 'bg-gray-300 text-white cursor-not-allowed' 
                      : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-[1.02] active:scale-100'
                  }`}
                >
                  {processingId === student.fiche ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      <span>{actionLabel}</span>
                      <ArrowRight className="h-5 w-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default QueueDesk;
