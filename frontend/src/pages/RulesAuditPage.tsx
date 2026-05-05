import React, { useEffect, useState } from 'react';
import { Loader2, ShieldCheck, ArrowDown, Info, BookOpen, Layers, ChevronRight } from 'lucide-react';
import client from '@/api/client';

// ── Types ──────────────────────────────────────────────────────────────────────

interface Constants {
  PASS_THRESHOLD: number;
  TEACHER_REVIEW_MIN: number;
  TEACHER_REVIEW_MAX: number;
  SUMMER_ELIGIBLE_MIN: number;
  SUMMER_ELIGIBLE_MAX: number;
  FAIL_HARD_BLOCK_THRESHOLD: number;
  MAX_SUMMER_CLASSES: number;
}

interface MicroRule {
  name: string;
  label: string;
  threshold_min: number | null;
  threshold_max: number | null;
  outcome_state: string;
  outcome_label: string;
  color: 'green' | 'orange' | 'yellow' | 'red';
  note: string | null;
}

interface PrecedenceRule {
  order: number;
  rule_key: string;
  label: string;
  trigger: string;
  outcome_workflow: string;
  outcome_label: string;
  note: string | null;
}

interface LevelRule {
  priority: number;
  condition: string;
  outcome_workflow: string;
  outcome_final: string | null;
  rule_key: string;
  label: string;
}

interface LevelPolicy {
  level_key: string;
  label: string;
  description: string;
  rules: LevelRule[];
}

interface AuditData {
  constants: Constants;
  micro_rules: MicroRule[];
  precedence: PrecedenceRule[];
  level_policies: LevelPolicy[];
}

// ── Color helpers ──────────────────────────────────────────────────────────────

const colorMap = {
  green:  { border: 'border-green-400',  bg: 'bg-green-50',  badge: 'bg-green-100 text-green-800 border-green-200',  dot: 'bg-green-500',  text: 'text-green-700' },
  orange: { border: 'border-orange-400', bg: 'bg-orange-50', badge: 'bg-orange-100 text-orange-800 border-orange-200', dot: 'bg-orange-500', text: 'text-orange-700' },
  yellow: { border: 'border-yellow-400', bg: 'bg-yellow-50', badge: 'bg-yellow-100 text-yellow-800 border-yellow-200', dot: 'bg-yellow-500', text: 'text-yellow-700' },
  red:    { border: 'border-red-400',    bg: 'bg-red-50',    badge: 'bg-red-100 text-red-800 border-red-200',          dot: 'bg-red-500',    text: 'text-red-700'   },
};

const outcomeWorkflowBadge = (w: string) => {
  if (w.includes('IFP'))      return 'bg-red-100 text-red-800 border border-red-200';
  if (w.includes('REGULAR'))  return 'bg-orange-100 text-orange-800 border border-orange-200';
  if (w.includes('READY'))    return 'bg-green-100 text-green-800 border border-green-200';
  return 'bg-gray-100 text-gray-700 border border-gray-200';
};

const outcomeFinalBadge = (f: string | null) => {
  if (!f) return null;
  if (f.includes('HOLDBACK')) return 'bg-red-100 text-red-800 border border-red-200';
  if (f.includes('SUMMER'))   return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
  if (f.includes('PROMOTE'))  return 'bg-green-100 text-green-800 border border-green-200';
  return 'bg-gray-100 text-gray-700 border border-gray-200';
};

// ── Grade range display ────────────────────────────────────────────────────────

function ThresholdRange({ min, max }: { min: number | null; max: number | null }) {
  if (min !== null && max !== null) return <span className="font-mono font-bold">{min} – {max}</span>;
  if (min !== null)                 return <span className="font-mono font-bold">≥ {min}</span>;
  if (max !== null)                 return <span className="font-mono font-bold">≤ {max}</span>;
  return <span className="font-mono text-gray-400">—</span>;
}

// ── Main component ─────────────────────────────────────────────────────────────

const RulesAuditPage: React.FC = () => {
  const [data, setData] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeLevel, setActiveLevel] = useState(0);

  useEffect(() => {
    client.get('/system/rules-audit')
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        <p className="text-gray-500 text-sm font-medium uppercase tracking-widest">Chargement des règles système...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center text-red-600 font-medium">
        Impossible de charger les règles. Vérifiez la connexion au serveur.
      </div>
    );
  }

  const { constants, micro_rules, precedence, level_policies } = data;

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-12">

      {/* ── Page header ── */}
      <div className="border-b-4 border-gray-900 pb-8">
        <div className="flex items-start gap-4">
          <div className="bg-blue-600 p-3 rounded-2xl">
            <BookOpen className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-black text-gray-900 uppercase tracking-tighter leading-none">
              Audit des Règles Système
            </h1>
            <p className="mt-2 text-gray-500 text-base leading-relaxed max-w-2xl">
              Cette page lit directement le code source du moteur de décision et traduit ses constantes en
              langage naturel. Toute modification d'un seuil dans le code se reflète ici automatiquement.
            </p>
          </div>
        </div>

        {/* Constants quick-reference bar */}
        <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(constants).map(([key, val]) => (
            <div key={key} className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3">
              <div className="text-[9px] font-black text-gray-400 uppercase tracking-widest font-mono">{key}</div>
              <div className="text-2xl font-black text-gray-900 mt-0.5">{val}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Section 1 : Micro-Rules (grade thresholds) ── */}
      <section className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="h-8 w-1 bg-blue-600 rounded-full" />
          <div>
            <h2 className="text-xl font-black text-gray-900 uppercase tracking-tight">1. Évaluation par Cours</h2>
            <p className="text-sm text-gray-500 mt-0.5">Comment chaque cours est classé individuellement avant l'agrégation macro.</p>
          </div>
        </div>

        <div className="space-y-4">
          {micro_rules.map((rule) => {
            const c = colorMap[rule.color];
            return (
              <div key={rule.name} className={`border-l-4 ${c.border} ${c.bg} rounded-r-2xl p-5`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${c.dot}`} />
                      <span className="text-xs font-black text-gray-500 uppercase tracking-widest">{rule.label}</span>
                    </div>
                    <p className="text-base font-bold text-gray-900">
                      {rule.threshold_min === null && rule.threshold_max === null
                        ? 'Note finale absente ou cas particulier'
                        : <>
                            Si la note finale est{' '}
                            <span className={`${c.text}`}>
                              <ThresholdRange min={rule.threshold_min} max={rule.threshold_max} />
                            </span>
                            , le cours est classé comme :{' '}
                            <span className={`inline-block px-2 py-0.5 text-xs font-black rounded border ${c.badge} font-mono`}>
                              {rule.outcome_state}
                            </span>
                          </>
                      }
                    </p>
                    <p className={`text-sm font-medium ${c.text}`}>{rule.outcome_label}</p>
                  </div>
                </div>
                {rule.note && (
                  <div className="mt-3 flex items-start gap-2 text-xs text-gray-600 bg-white/60 rounded-xl px-3 py-2">
                    <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-gray-400" />
                    <span>{rule.note}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Section 2 : Precedence chain ── */}
      <section className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="h-8 w-1 bg-purple-600 rounded-full" />
          <div>
            <h2 className="text-xl font-black text-gray-900 uppercase tracking-tight">2. Ordre de Priorité</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Le moteur évalue les règles dans cet ordre exact. La première règle déclenchée s'applique — les suivantes sont ignorées.
            </p>
          </div>
        </div>

        <div className="relative space-y-3">
          {precedence.map((rule, idx) => (
            <div key={rule.rule_key} className="relative flex gap-4">
              {/* Connector line */}
              {idx < precedence.length - 1 && (
                <div className="absolute left-5 top-12 bottom-[-12px] w-px bg-gray-200" />
              )}

              {/* Order badge */}
              <div className="shrink-0 h-10 w-10 rounded-full bg-purple-600 text-white flex items-center justify-center font-black text-sm z-10">
                {rule.order}
              </div>

              <div className="flex-1 bg-white border-2 border-gray-100 rounded-2xl p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-black text-gray-900 text-base">{rule.label}</span>
                  <span className="text-[9px] font-black font-mono text-gray-400 bg-gray-100 px-2 py-0.5 rounded border border-gray-200">
                    {rule.rule_key}
                  </span>
                </div>
                <p className="text-sm text-gray-700">
                  <span className="font-bold text-gray-500 uppercase text-[10px] tracking-widest block mb-1">Déclencheur</span>
                  {rule.trigger}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Résultat :</span>
                  <span className={`text-xs font-black px-2 py-0.5 rounded font-mono ${outcomeWorkflowBadge(rule.outcome_workflow)}`}>
                    {rule.outcome_workflow}
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 text-gray-300" />
                  <span className="text-sm font-medium text-gray-600 italic">{rule.outcome_label}</span>
                </div>
                {rule.note && (
                  <div className="flex items-start gap-2 text-xs text-gray-600 bg-purple-50 rounded-xl px-3 py-2">
                    <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-purple-400" />
                    <span>{rule.note}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          <div className="flex gap-4">
            <div className="shrink-0 h-10 w-10 flex items-center justify-center">
              <ArrowDown className="h-5 w-5 text-gray-300" />
            </div>
            <div className="flex-1 bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-5 flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-500 italic">Politique spécifique au niveau de l'élève (voir section 3)</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 3 : Level policies ── */}
      <section className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="h-8 w-1 bg-gray-900 rounded-full" />
          <div>
            <h2 className="text-xl font-black text-gray-900 uppercase tracking-tight">3. Politiques par Niveau</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Une fois les règles de priorité épuisées, le moteur applique la politique propre au niveau de l'élève.
            </p>
          </div>
        </div>

        {/* Level tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 w-fit">
          {level_policies.map((policy, idx) => (
            <button
              key={policy.level_key}
              onClick={() => setActiveLevel(idx)}
              className={`px-4 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${
                activeLevel === idx
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {policy.label}
            </button>
          ))}
        </div>

        {/* Active policy */}
        {level_policies[activeLevel] && (() => {
          const policy = level_policies[activeLevel];
          return (
            <div className="bg-white border-2 border-gray-100 rounded-2xl overflow-hidden">
              <div className="bg-gray-50 border-b-2 border-gray-100 px-6 py-4">
                <div className="flex items-center gap-2 mb-1">
                  <Layers className="h-4 w-4 text-gray-400" />
                  <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{policy.level_key}</span>
                </div>
                <h3 className="text-lg font-black text-gray-900">{policy.label}</h3>
                <p className="text-sm text-gray-600 mt-1 italic">{policy.description}</p>
              </div>

              <div className="divide-y divide-gray-50">
                {policy.rules.map((rule) => (
                  <div key={rule.rule_key} className="px-6 py-5 flex gap-5">
                    {/* Priority number */}
                    <div className="shrink-0 h-7 w-7 rounded-full bg-gray-100 border-2 border-gray-200 flex items-center justify-center text-xs font-black text-gray-600">
                      {rule.priority}
                    </div>

                    <div className="flex-1 space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-black text-gray-900">{rule.label}</span>
                        <span className="text-[9px] font-black font-mono text-gray-400 bg-gray-100 px-2 py-0.5 rounded border border-gray-200">
                          {rule.rule_key}
                        </span>
                      </div>

                      <p className="text-sm text-gray-700">
                        <span className="font-semibold">Condition : </span>
                        {rule.condition}
                      </p>

                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Résultat :</span>
                        <span className={`text-xs font-black px-2 py-0.5 rounded font-mono ${outcomeWorkflowBadge(rule.outcome_workflow)}`}>
                          {rule.outcome_workflow}
                        </span>
                        {rule.outcome_final && (
                          <>
                            <span className="text-gray-300 text-xs">+</span>
                            <span className={`text-xs font-black px-2 py-0.5 rounded font-mono ${outcomeFinalBadge(rule.outcome_final)}`}>
                              {rule.outcome_final}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}
      </section>

      {/* ── Footer ── */}
      <footer className="border-t-2 border-gray-100 pt-6 pb-2 text-center">
        <p className="text-xs text-gray-400 font-medium">
          Documentation générée dynamiquement depuis{' '}
          <code className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">students/constants.py</code>
          {' '}et{' '}
          <code className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">students/services/auto_derivation.py</code>.
          Aucune valeur n'est codée en dur dans cette interface.
        </p>
      </footer>
    </div>
  );
};

export default RulesAuditPage;
