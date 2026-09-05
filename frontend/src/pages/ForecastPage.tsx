import React, { useState, useEffect } from 'react';
import { forecastApi } from '../services/forecastApi';
import { RevenueForecastResponse, ForecastExplanationResponse } from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { ForecastConfidenceCard } from '../components/intelligence/ForecastConfidenceCard';
import { ForecastDealTable } from '../components/intelligence/ForecastDealTable';
import { TrendingUp, AlertTriangle, Sparkles, RefreshCw, Layers, ShieldAlert, CheckCircle } from 'lucide-react';

export const ForecastPage: React.FC = () => {
  const { showToast } = useToast();

  const [forecast, setForecast] = useState<RevenueForecastResponse | null>(null);
  const [aiExplanation, setAiExplanation] = useState<ForecastExplanationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scenarios & Filters
  const [selectedScenario, setSelectedScenario] = useState<'base' | 'conservative' | 'optimistic'>('base');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const loadForecast = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await forecastApi.getForecast({
        period: selectedPeriod !== 'all' ? selectedPeriod : undefined,
        forecast_category: selectedCategory !== 'all' ? selectedCategory : undefined,
      });
      setForecast(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load revenue forecast data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [selectedPeriod, selectedCategory]);

  const handleGenerateAiExplanation = async () => {
    setIsAiLoading(true);
    try {
      const res = await forecastApi.getForecastExplanation();
      setAiExplanation(res);
      showToast('AI Executive Revenue Forecast explanation generated.', 'ai');
    } catch (err: any) {
      showToast(err.message || 'Failed to generate AI explanation.', 'error');
    } finally {
      setIsAiLoading(false);
    }
  };

  if (isLoading) return <LoadingState message="Calculating deterministic revenue forecast & scenario projections..." />;
  if (error || !forecast) return <ErrorState message={error || 'Forecast data unavailable'} onRetry={loadForecast} />;

  const isHighConf = forecast.confidence_score >= 80;
  const isModConf = forecast.confidence_score >= 60 && forecast.confidence_score < 80;

  // Active scenario revenue display
  const activeScenarioRevenue =
    selectedScenario === 'conservative'
      ? forecast.scenarios.conservative_revenue
      : selectedScenario === 'optimistic'
      ? forecast.scenarios.optimistic_revenue
      : forecast.forecast_revenue;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs font-bold uppercase tracking-widest">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Executive Revenue Forecast Command Center</span>
          </div>
          <h1 className="text-3xl font-black text-slate-100 tracking-tight mt-1">Revenue Forecast & Predictions</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Deterministic revenue engine, scenario modeling, coverage telemetry, and AI advisory commentary
          </p>
        </div>

        <div className="flex items-center gap-3">
          <BrutalButton
            variant="ghost"
            size="sm"
            icon={RefreshCw}
            onClick={loadForecast}
          >
            Refresh Model
          </BrutalButton>

          <BrutalButton
            variant="ai"
            size="sm"
            icon={Sparkles}
            onClick={handleGenerateAiExplanation}
            isLoading={isAiLoading}
          >
            ✦ AI Advisory Commentary
          </BrutalButton>
        </div>
      </div>

      {/* Scenario Model Selector Switcher */}
      <div className="p-4 rounded-2xl bg-slate-950/90 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span className="font-bold uppercase tracking-wider">Forecast Model Scenario:</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedScenario('conservative')}
            className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold uppercase transition ${
              selectedScenario === 'conservative'
                ? 'bg-cyan-600 text-white border-cyan-400 shadow-md shadow-cyan-900/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Conservative (${Number(forecast.scenarios.conservative_revenue).toLocaleString()})
          </button>

          <button
            onClick={() => setSelectedScenario('base')}
            className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold uppercase transition ${
              selectedScenario === 'base'
                ? 'bg-emerald-600 text-white border-emerald-400 shadow-md shadow-emerald-900/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Base Model (${Number(forecast.forecast_revenue).toLocaleString()})
          </button>

          <button
            onClick={() => setSelectedScenario('optimistic')}
            className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold uppercase transition ${
              selectedScenario === 'optimistic'
                ? 'bg-indigo-600 text-white border-indigo-400 shadow-md shadow-indigo-900/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Optimistic (${Number(forecast.scenarios.optimistic_revenue).toLocaleString()})
          </button>
        </div>
      </div>

      {/* Primary KPI Hero Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <GlassCard className="p-5 border-l-4 border-l-emerald-500 bg-emerald-950/10">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">
            {selectedScenario.toUpperCase()} FORECAST REVENUE
          </span>
          <span className="text-2xl font-black text-emerald-400 block mt-1">
            ${Number(activeScenarioRevenue).toLocaleString()}
          </span>
          <span className="text-[10px] text-slate-500 block mt-1">
            {selectedScenario === 'conservative'
              ? 'High Confidence Committed Only'
              : selectedScenario === 'optimistic'
              ? 'Committed + Upside + High-Prob Pipeline'
              : 'Deterministic Adjusted Probability Sum'}
          </span>
        </GlassCard>

        <GlassCard className="p-5 border-l-4 border-l-indigo-500 bg-indigo-950/10">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Forecast Confidence</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-2xl font-black ${isHighConf ? 'text-emerald-400' : isModConf ? 'text-indigo-300' : 'text-rose-400'}`}>
              {forecast.confidence_score}/100
            </span>
            <span className="text-[10px] text-indigo-300 font-bold uppercase">{forecast.confidence_label}</span>
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">Deterministic Quality Score</span>
        </GlassCard>

        <GlassCard className="p-5 border-l-4 border-l-cyan-500 bg-cyan-950/10">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Pipeline Coverage Ratio</span>
          <span className="text-2xl font-bold text-cyan-300 block mt-1">
            {forecast.coverage_ratio}x
          </span>
          <span className="text-[10px] text-slate-500 block mt-1">Open Pipeline vs Base Forecast</span>
        </GlassCard>

        <GlassCard className="p-5 border-l-4 border-l-rose-500 bg-rose-950/10">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">At-Risk Revenue</span>
          <span className="text-2xl font-bold text-rose-400 block mt-1">
            ${Number(forecast.at_risk_revenue).toLocaleString()}
          </span>
          <span className="text-[10px] text-slate-500 block mt-1">Requires Sales Intervention</span>
        </GlassCard>
      </div>

      {/* Pipeline Financial Comparison & Concentration Banner */}
      <GlassCard title="Pipeline Financial Comparison & Velocity">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono text-center mb-4">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Open Pipeline</span>
            <span className="text-lg font-bold text-slate-200">${Number(forecast.open_pipeline).toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Weighted Pipeline</span>
            <span className="text-lg font-bold text-sky-400">${Number(forecast.weighted_pipeline).toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/80 border border-emerald-500/30">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Committed Revenue</span>
            <span className="text-lg font-bold text-cyan-300">${Number(forecast.committed_revenue).toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/80 border border-indigo-500/30">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Won Revenue</span>
            <span className="text-lg font-bold text-indigo-300">${Number(forecast.won_revenue).toLocaleString()}</span>
          </div>
        </div>

        {forecast.concentration_risk && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-xs font-mono text-amber-200">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold uppercase tracking-wider block">⚠ FORECAST CONCENTRATION RISK DETECTED</span>
              <span>A small number of high-value deals account for over 50% of total expected pipeline revenue.</span>
            </div>
          </div>
        )}
      </GlassCard>

      {/* Period Telemetry Cards */}
      <div>
        <span className="text-xs font-mono font-bold text-indigo-400 uppercase tracking-widest block mb-3">
          Forecast Telemetry by Close Period
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
          {forecast.periods.map((p) => (
            <div
              key={p.period_key}
              onClick={() => setSelectedPeriod(selectedPeriod === p.period_key ? 'all' : p.period_key)}
              className={`p-4 rounded-xl bg-slate-950/80 border transition cursor-pointer hover:border-indigo-500/60 ${
                selectedPeriod === p.period_key ? 'border-2 border-indigo-500 bg-indigo-950/20' : 'border-slate-800'
              }`}
            >
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-slate-100 text-xs">{p.period_label}</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                  {p.deal_count} deals
                </span>
              </div>

              <div className="space-y-1 pt-2 border-t border-slate-800 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Forecast:</span>
                  <span className="font-bold text-emerald-400">${Number(p.forecast_revenue).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Committed:</span>
                  <span className="text-cyan-300">${Number(p.committed_revenue).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">At Risk:</span>
                  <span className="text-rose-400">${Number(p.at_risk_revenue).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Explanation Card */}
      {aiExplanation && (
        <AIInsightCard
          title="AI Executive Revenue Forecast Commentary"
          provider="DealFlow360 Intelligence Engine"
          model="Read-Only Advisory Model"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="p-3.5 bg-slate-950/90 rounded-xl border border-indigo-500/30 text-slate-200 leading-relaxed">
              {aiExplanation.summary}
            </div>

            {aiExplanation.risk_highlights.length > 0 && (
              <div className="p-3 rounded-xl bg-rose-950/10 border border-rose-500/20 space-y-1.5">
                <span className="font-bold text-rose-300 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  Key Risk Highlights
                </span>
                <ul className="space-y-1 text-slate-300 text-[11px]">
                  {aiExplanation.risk_highlights.map((rh, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-rose-400 font-bold">•</span>
                      <span>{rh}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {aiExplanation.recommendations.length > 0 && (
              <div className="p-3 rounded-xl bg-emerald-950/10 border border-emerald-500/20 space-y-1.5">
                <span className="font-bold text-emerald-300 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  Actionable Interventions
                </span>
                <ul className="space-y-1 text-slate-300 text-[11px]">
                  {aiExplanation.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </AIInsightCard>
      )}

      {/* Forecast Confidence Rationale Card */}
      <ForecastConfidenceCard forecast={forecast} />

      {/* Deal Level Forecast Table with Filters */}
      <GlassCard
        title={
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <span>Opportunity Level Forecast Classification ({forecast.deals.length})</span>
            <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
              <span className="text-slate-400 uppercase text-[10px] font-bold">Category:</span>
              {['all', 'COMMITTED', 'UPSIDE', 'PIPELINE', 'AT_RISK'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-lg border text-[11px] font-bold uppercase transition ${
                    selectedCategory === cat
                      ? 'bg-indigo-600 text-white border-indigo-500'
                      : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        }
        subtitle="Individual deal probability adjustments, forecast categories, and rationale"
      >
        <ForecastDealTable deals={forecast.deals} />
      </GlassCard>
    </div>
  );
};

