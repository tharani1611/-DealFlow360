import React, { useState, useEffect } from 'react';
import { NegotiationSimulationResponse, SimulationScenario } from '../../types';
import { negotiationApi } from '../../services/negotiationApi';
import {
  Bot,
  ShieldCheck,
  TrendingUp,
  Award,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  X,
  RefreshCw,
  Zap,
} from 'lucide-react';

interface CoNegotiatorSimulatorModalProps {
  quotationId: string;
  quotationNumber: string;
  initialDiscountPercent?: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const CoNegotiatorSimulatorModal: React.FC<CoNegotiatorSimulatorModalProps> = ({
  quotationId,
  quotationNumber,
  initialDiscountPercent = 12.0,
  onClose,
  onSuccess,
}) => {
  const [requestedDiscount, setRequestedDiscount] = useState<number>(initialDiscountPercent);
  const [targetWinProb, setTargetWinProb] = useState<number>(80);
  const [loading, setLoading] = useState<boolean>(true);
  const [applying, setApplying] = useState<string | null>(null);
  const [simulationData, setSimulationData] = useState<NegotiationSimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedScenarioId, setCopiedScenarioId] = useState<string | null>(null);

  const runSimulation = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await negotiationApi.simulateCounterOffer(quotationId, {
        requested_discount_percent: requestedDiscount,
        target_win_probability: targetWinProb,
      });
      setSimulationData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to execute negotiation scenario simulation');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, []);

  const handleApplyCounterOffer = async (scenario: SimulationScenario) => {
    try {
      setApplying(scenario.scenario_id);
      setError(null);
      await negotiationApi.applyCounterDiscount(quotationId, {
        requested_discount_percent: parseFloat(scenario.recommended_discount_percent),
        change_reason: `AI Co-Negotiator Recommendation (${scenario.strategy_type}): ${scenario.reasoning_summary}`,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to apply counter-offer');
    } finally {
      setApplying(null);
    }
  };

  const handleCopyScript = (scenario: SimulationScenario) => {
    navigator.clipboard.writeText(scenario.counter_proposal_script);
    setCopiedScenarioId(scenario.scenario_id);
    setTimeout(() => setCopiedScenarioId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/60 rounded-3xl max-w-4xl w-full overflow-hidden shadow-2xl my-8">
        {/* Header */}
        <div className="p-5 bg-gradient-to-r from-slate-900 via-indigo-950/50 to-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl text-indigo-400">
              <Bot className="w-6 h-6 animate-pulse text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white tracking-tight">
                  Autonomous AI Co-Negotiator & Counter-Offer Simulator
                </h3>
                <span className="px-2.5 py-0.5 text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-indigo-400" /> 120+ Scenarios
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Simulating margin thresholds, win rates, and commercial counter-proposals for <span className="text-slate-200 font-mono">{quotationNumber}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Controls Bar */}
          <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-2xl grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center justify-between">
                <span>Requested Discount Target</span>
                <span className="text-indigo-400 font-mono">{requestedDiscount.toFixed(1)}%</span>
              </label>
              <div className="relative flex items-center">
                <input
                  type="range"
                  min="1"
                  max="35"
                  step="0.5"
                  value={requestedDiscount}
                  onChange={(e) => setRequestedDiscount(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center justify-between">
                <span>Target Deal Win Rate</span>
                <span className="text-emerald-400 font-mono">{targetWinProb}%</span>
              </label>
              <div className="relative flex items-center">
                <input
                  type="range"
                  min="40"
                  max="95"
                  step="5"
                  value={targetWinProb}
                  onChange={(e) => setTargetWinProb(parseInt(e.target.value))}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
              </div>
            </div>

            <div className="flex items-end justify-end">
              <button
                onClick={runSimulation}
                disabled={loading}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Simulating 120 Scenarios...' : 'Re-Run AI Scenario Simulation'}
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="py-16 text-center space-y-4">
              <div className="relative w-16 h-16 mx-auto">
                <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping"></div>
                <div className="relative w-16 h-16 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin flex items-center justify-center">
                  <Bot className="w-6 h-6 text-indigo-400" />
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Simulating 120 Micro-Negotiation Outcomes...</p>
                <p className="text-xs text-slate-400">Evaluating margin sensitivity, inventory volume, and perk swaps</p>
              </div>
            </div>
          ) : simulationData ? (
            <div className="space-y-6">
              {/* Baseline Summary Pill */}
              <div className="flex flex-wrap items-center justify-between gap-4 p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl text-xs">
                <div className="flex items-center gap-4 text-slate-300">
                  <span>
                    Baseline Subtotal: <strong className="text-white font-mono">₹{parseFloat(simulationData.original_total).toLocaleString('en-IN')}</strong>
                  </span>
                  <span className="text-slate-600">•</span>
                  <span>
                    Gross Margin: <strong className="text-emerald-400 font-mono">{simulationData.original_margin_percent}%</strong>
                  </span>
                </div>
                <span className="text-indigo-400 font-medium flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" /> Evaluated {simulationData.simulated_scenarios_count} scenarios
                </span>
              </div>

              {/* 3 Strategy Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {simulationData.recommended_scenarios.map((scenario) => {
                  const isBalanced = scenario.strategy_type === 'BALANCED';
                  const isVolume = scenario.strategy_type === 'VOLUME_INCENTIVE';

                  const borderClass = isBalanced
                    ? 'border-indigo-500/40 hover:border-indigo-500'
                    : isVolume
                    ? 'border-emerald-500/40 hover:border-emerald-500'
                    : 'border-amber-500/40 hover:border-amber-500';

                  const badgeClass = isBalanced
                    ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                    : isVolume
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30';

                  const icon = isBalanced ? (
                    <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  ) : isVolume ? (
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Award className="w-4 h-4 text-amber-400" />
                  );

                  return (
                    <div
                      key={scenario.scenario_id}
                      className={`bg-slate-800/40 border ${borderClass} rounded-2xl p-5 flex flex-col justify-between transition-all duration-200 hover:shadow-xl hover:bg-slate-800/70`}
                    >
                      <div className="space-y-4">
                        {/* Strategy Header */}
                        <div>
                          <div className="flex items-center justify-between gap-2 mb-2">
                            <span className={`px-2.5 py-1 text-[10px] font-bold border rounded-lg flex items-center gap-1.5 ${badgeClass}`}>
                              {icon} {scenario.strategy_type}
                            </span>
                            <span className="text-[11px] font-bold text-emerald-400 font-mono">
                              {scenario.simulated_win_probability}% Win Prob
                            </span>
                          </div>
                          <h4 className="text-sm font-bold text-white">{scenario.title}</h4>
                        </div>

                        {/* Win Probability Bar */}
                        <div>
                          <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isBalanced ? 'bg-indigo-500' : isVolume ? 'bg-emerald-500' : 'bg-amber-500'
                              }`}
                              style={{ width: `${scenario.simulated_win_probability}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Key Financial Impact Grid */}
                        <div className="grid grid-cols-2 gap-2 text-xs bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                          <div>
                            <span className="text-slate-400 block text-[10px]">Counter Discount</span>
                            <span className="text-white font-bold font-mono">{scenario.recommended_discount_percent}%</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[10px]">Commitment</span>
                            <span className="text-white font-bold font-mono">{scenario.recommended_volume_commitment} units</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[10px]">Projected Margin</span>
                            <span className="text-emerald-400 font-bold font-mono">{scenario.projected_gross_margin_percent}%</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[10px]">Net Profit</span>
                            <span className="text-indigo-300 font-bold font-mono">
                              ₹{parseFloat(scenario.projected_net_profit).toLocaleString('en-IN')}
                            </span>
                          </div>
                        </div>

                        {/* Perks */}
                        <div>
                          <span className="text-[11px] font-semibold text-slate-300 block mb-1.5">Value-Add Perks Swapped:</span>
                          <div className="space-y-1">
                            {scenario.offered_perks.map((perk, idx) => (
                              <div key={idx} className="flex items-center gap-1.5 text-xs text-slate-300">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                <span>{perk}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* AI Script & Reasoning */}
                        <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">
                              AI Pitch Script
                            </span>
                            <button
                              type="button"
                              onClick={() => handleCopyScript(scenario)}
                              className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1"
                            >
                              {copiedScenarioId === scenario.scenario_id ? (
                                <Check className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                              {copiedScenarioId === scenario.scenario_id ? 'Copied' : 'Copy'}
                            </button>
                          </div>
                          <p className="text-[11px] text-slate-300 italic leading-relaxed">
                            "{scenario.counter_proposal_script}"
                          </p>
                        </div>
                      </div>

                      {/* Action Button */}
                      <div className="pt-4 border-t border-slate-800/80 mt-4">
                        <button
                          type="button"
                          disabled={!!applying}
                          onClick={() => handleApplyCounterOffer(scenario)}
                          className={`w-full py-2.5 px-3 text-xs font-bold rounded-xl transition flex items-center justify-center gap-2 ${
                            isBalanced
                              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                              : isVolume
                              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20'
                              : 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-600/20'
                          } disabled:opacity-50`}
                        >
                          {applying === scenario.scenario_id ? (
                            'Applying Strategy...'
                          ) : (
                            <>
                              <Zap className="w-3.5 h-3.5" />
                              Apply Strategy to Quote
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> Guards gross margin thresholds & prevents baseline price erosion automatically.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
          >
            Close Simulator
          </button>
        </div>
      </div>
    </div>
  );
};
