import React, { useState } from 'react';
import TriageMatrix from '@/components/TriageMatrix';
import { BarChart3 } from 'lucide-react';

const TriageMatrixPage: React.FC = () => {
  const [academicYear, setAcademicYear] = useState('2025-2026');
  const [level, setLevel] = useState('2');

  const years = ['2023-2024', '2024-2025', '2025-2026'];
  const levels = ['1', '2', '3', '4', '5'];

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="md:flex md:items-center md:justify-between mb-8">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            Matrice de Triage
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Analyse de la répartition des échecs par niveau et année académique.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-8">
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex flex-wrap gap-4 items-center">
          <div>
            <label htmlFor="year" className="block text-xs font-medium text-gray-700 uppercase tracking-wider mb-1">
              Année Académique
            </label>
            <select
              id="year"
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              {years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="level" className="block text-xs font-medium text-gray-700 uppercase tracking-wider mb-1">
              Niveau
            </label>
            <select
              id="level"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              {levels.map((l) => (
                <option key={l} value={l}>Secondaire {l}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="p-6">
          <TriageMatrix academicYear={academicYear} level={level} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-100 text-blue-800">
          <h3 className="font-bold mb-2">Guide de lecture</h3>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>L'axe vertical (lignes) représente le <strong>nombre total d'échecs</strong> de l'élève.</li>
            <li>L'axe horizontal (colonnes) représente le <strong>nombre d'échecs dans les matières de base</strong> (Français, Mathématiques, Anglais, etc.).</li>
            <li>Les cases grisées sont impossibles (on ne peut pas avoir plus d'échecs de base que d'échecs totaux).</li>
          </ul>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 text-gray-700">
          <h3 className="font-bold mb-2">Actions disponibles</h3>
          <p className="text-sm">
            Cliquez sur une case contenant des élèves pour afficher la liste détaillée et procéder au classement manuel ou automatisé.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TriageMatrixPage;
