import React from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import { RevenueForecastResponse } from '../../types';
import { GlassCard } from '../ui/GlassCard';
import { BrutalButton } from '../ui/BrutalButton';

interface RevenueForecastCardProps {
  forecast: RevenueForecastResponse;
}

export const RevenueForecastCard: React.FC<RevenueForecastCardProps> = ({ forecast }) => {
  const navigate = useNavigate();

  const isHighConf = forecast.confidence_score >= 80;
  const isModConf = forecast.confidence_score >= 60 && forecast.confidence_score < 80;

  return (
    <GlassCard className="border-2 border-indigo-500/40 p-6 shadow-glass-glow">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs font-bold uppercase tracking-widest">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Deterministic Revenue Forecast</span>
          </div>
          <h2 className="text-xl font-black text-slate-100 tracking-tight mt-0.5">Pipeline Prediction Model</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold border flex items-center gap-1.5 ${
            isHighConf
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
              : isModConf
              ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
              : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
          }`}>
            <ShieldCheck className="w-4 h-4" />
            <span>{forecast.confidence_score}/100</span>
            <span className="text-[10px] opacity-80 uppercase">• {forecast.confidence_label}</span>
          </div>

          <BrutalButton
            variant="primary"
            size="sm"
            icon={ArrowRight}
            onClick={() => navigate('/forecast')}
          >
            View Forecast
          </BrutalButton>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6 text-center font-mono">
        <div className="p-3 bg-black/40 rounded-xl border border-indigo-500/30">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Forecast Revenue</span>
          <span className="text-xl font-black text-emerald-400">${Number(forecast.forecast_revenue).toLocaleString()}</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Adjusted Probability Total</span>
        </div>

        <div className="p-3 bg-black/40 rounded-xl border border-emerald-500/30">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Committed Revenue</span>
          <span className="text-xl font-bold text-cyan-300">${Number(forecast.committed_revenue).toLocaleString()}</span>
          <span className="text-[10px] text-emerald-400 block mt-0.5">High Confidence Deals</span>
        </div>

        <div className="p-3 bg-black/40 rounded-xl border border-rose-500/30">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">At Risk Revenue</span>
          <span className="text-xl font-bold text-rose-400">${Number(forecast.at_risk_revenue).toLocaleString()}</span>
          <span className="text-[10px] text-rose-300 block mt-0.5">Requires Action</span>
        </div>

        <div className="p-3 bg-black/40 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Open Pipeline</span>
          <span className="text-xl font-bold text-slate-200">${Number(forecast.open_pipeline).toLocaleString()}</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Unweighted Value</span>
        </div>
      </div>

      {/* Concentration Risk Banner */}
      {forecast.concentration_risk && (
        <div className="mb-6 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-xs font-mono text-amber-200">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
          <div>
            <span className="font-bold uppercase tracking-wider block">Forecast Concentration Risk</span>
            <span>A small number of high-value deals represent over 50% of your open pipeline revenue.</span>
          </div>
        </div>
      )}

      {/* Period Breakdown Preview */}
      <div className="pt-4 border-t border-slate-800">
        <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest block mb-3">
          Expected Close Period Telemetry
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          {forecast.periods.filter(p => p.period_key !== 'no_close_date').slice(0, 3).map((p) => (
            <div key={p.period_key} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex justify-between items-center">
              <div>
                <span className="font-bold text-slate-200 block text-[11px]">{p.period_label}</span>
                <span className="text-[10px] text-slate-500">{p.deal_count} active deal(s)</span>
              </div>
              <div className="text-right">
                <span className="font-bold text-emerald-400 text-sm">${Number(p.forecast_revenue).toLocaleString()}</span>
                <span className="text-[10px] text-slate-400 block">${Number(p.committed_revenue).toLocaleString()} committed</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </GlassCard>
  );
};
