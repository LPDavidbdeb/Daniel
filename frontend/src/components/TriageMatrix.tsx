import React, { useEffect, useState } from 'react';
import client from '@/api/client';

interface TriageMatrixItem {
  total_failures: number;
  core_failures: number;
  student_count: number;
}

interface TriageDrilldownItem {
  subject: string;
  grade_band: string;
  failure_count: number;
}

interface TriageMatrixProps {
  academicYear: string;
  level: string;
}

const TriageMatrix: React.FC<TriageMatrixProps> = ({ academicYear, level }) => {
  const [data, setData] = useState<TriageMatrixItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Drilldown state
  const [selectedBucket, setSelectedBucket] = useState<{ total: number; core: number } | null>(null);
  const [drilldownData, setDrilldownData] = useState<TriageDrilldownItem[]>([]);
  const [drilldownLoading, setDrilldownLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setSelectedBucket(null);
      setDrilldownData([]);
      try {
        const response = await client.get<TriageMatrixItem[]>(
          `/students/triage-matrix/${academicYear}/${level}`
        );
        setData(response.data);
      } catch (err) {
        console.error('Failed to fetch triage matrix data:', err);
        setError('Erreur lors du chargement des données.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [academicYear, level]);

  const fetchDrilldown = async (total: number, core: number) => {
    setDrilldownLoading(true);
    try {
      const response = await client.get<TriageDrilldownItem[]>(
        `/students/triage-drilldown/${academicYear}/${level}`,
        { params: { total_fails: total, core_fails: core } }
      );
      setDrilldownData(response.data);
    } catch (err) {
      console.error('Failed to fetch drilldown data:', err);
    } finally {
      setDrilldownLoading(false);
    }
  };

  const handleCellClick = (total: number, core: number, count: number) => {
    if (count === 0) return;
    setSelectedBucket({ total, core });
    fetchDrilldown(total, core);
  };

  const maxTotalFailures = 6;
  const maxCoreFailures = 4;

  const totalFailuresRange = Array.from({ length: maxTotalFailures + 1 }, (_, i) => i);
  const coreFailuresRange = Array.from({ length: maxCoreFailures + 1 }, (_, i) => i);

  const getStudentCount = (total: number, core: number) => {
    const item = data.find(
      (d) => d.total_failures === total && d.core_failures === core
    );
    return item ? item.student_count : 0;
  };

  const gradeBands = ['Below 45', '45-49', '50-54', '55-59'];

  if (loading) return <div className="p-4 text-center">Chargement de la matrice...</div>;
  if (error) return <div className="p-4 text-center text-red-500">{error}</div>;

  // Transform drilldown data for display
  const subjects = Array.from(new Set(drilldownData.map((d) => d.subject))).sort();

  return (
    <div className="space-y-8 p-4">
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse border border-gray-300 bg-white shadow-sm">
          <thead>
            <tr>
              <th className="border border-gray-300 bg-gray-100 p-2 text-xs font-medium uppercase text-gray-600">
                Total \ Core
              </th>
              {coreFailuresRange.map((core) => (
                <th
                  key={core}
                  className="border border-gray-300 bg-gray-100 p-2 text-xs font-medium uppercase text-gray-600"
                >
                  {core === maxCoreFailures ? `${core}+` : core}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {totalFailuresRange.map((total) => (
              <tr key={total}>
                <td className="border border-gray-300 bg-gray-100 p-2 text-center text-xs font-bold text-gray-600">
                  {total === maxTotalFailures ? `${total}+` : total}
                </td>
                {coreFailuresRange.map((core) => {
                  const isImpossible = core > total;
                  const count = getStudentCount(total, core);
                  const isSelected = selectedBucket?.total === total && selectedBucket?.core === core;

                  return (
                    <td
                      key={`${total}-${core}`}
                      onClick={() => !isImpossible && handleCellClick(total, core, count)}
                      className={`
                        border border-gray-300 p-4 text-center text-sm transition-all
                        ${isImpossible ? 'bg-gray-200 cursor-not-allowed' : 'hover:bg-blue-50 cursor-pointer'}
                        ${isSelected ? 'ring-2 ring-inset ring-blue-500 bg-blue-100 font-bold' : ''}
                        ${count > 0 ? 'text-blue-700' : 'text-gray-400'}
                      `}
                    >
                      {!isImpossible ? count : '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedBucket && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Détails des échecs : {selectedBucket.total} échecs totaux, {selectedBucket.core} échecs de base
            </h3>
            {drilldownLoading && <span className="text-sm text-blue-600 animate-pulse">Chargement des détails...</span>}
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse border border-gray-300 bg-white shadow-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-300 p-2 text-left text-xs font-medium uppercase text-gray-600">
                    Matière (Sujet)
                  </th>
                  {gradeBands.map((band) => (
                    <th key={band} className="border border-gray-300 p-2 text-center text-xs font-medium uppercase text-gray-600">
                      {band === 'Below 45' ? '< 45' : band}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {subjects.length > 0 ? (
                  subjects.map((subject) => (
                    <tr key={subject} className="hover:bg-gray-50">
                      <td className="border border-gray-300 p-2 text-sm font-medium text-gray-800">
                        {subject}
                      </td>
                      {gradeBands.map((band) => {
                        const drill = drilldownData.find(
                          (d) => d.subject === subject && d.grade_band === band
                        );
                        return (
                          <td key={band} className="border border-gray-300 p-2 text-center text-sm">
                            {drill ? (
                              <span className={`px-2 py-1 rounded ${drill.failure_count > 0 ? 'bg-red-50 text-red-700 font-semibold' : ''}`}>
                                {drill.failure_count}
                              </span>
                            ) : '0'}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={gradeBands.length + 1} className="p-8 text-center text-gray-500 italic">
                      {drilldownLoading ? 'Récupération des données...' : 'Aucune donnée disponible pour ce bucket.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default TriageMatrix;
