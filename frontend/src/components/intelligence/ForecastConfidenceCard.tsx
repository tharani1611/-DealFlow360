import React from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle } from 'lucide-react';
import { RevenueForecastResponse } from '../../types';
import { GlassCard } from '../ui/GlassCard';

interface ForecastConfidenceCardProps {
  forecast: RevenueForecastResponse;
}

export const ForecastConfidenceCard: React.FC<ForecastConfidenceCardProps> = ({ forecast }) => {
  const isHighConf = forecast.confidence_score >= 80;
  const isModConf = forecast.confidence_score >= 60 && forecast.confidence_score < 80;

  return (
    <GlassCard
      title={
        <div className="flex items-center gap-2 text-indigo-300">
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
          <span>Forecast Confidence & Telemetry Analysis</span>
        </div>
      }
      subtitle="Deterministic scoring based on deal health, activity recency, and value distribution"
    >
      <div className="space-y-4 font-mono text-xs">
        {/* Score Display Header */}
        <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Overall Confidence Score</span>
            <span className={`text-2xl font-black ${
              isHighConf ? 'text-emerald-400' : isModConf ? 'text-indigo-300' : 'text-rose-400'
            }`}>
              {forecast.confidence_score} / 100
            </span>
          </div>

          <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase ${
            isHighConf
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
              : isModConf
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
              : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
          }`}>
            {forecast.confidence_label}
          </span>
        </div>

        {/* Contributing Factors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Positive Drivers */}
          <div className="p-3.5 rounded-xl bg-emerald-950/10 border border-emerald-500/20 space-y-2">
            <h4 className="font-bold text-emerald-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Positive Forecast Drivers
            </h4>
            {forecast.confidence_factors.positive_factors.length > 0 ? (
              <ul className="space-y-1 text-slate-300 text-[11px] leading-relaxed">
                {forecast.confidence_factors.positive_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500 text-[11px]">No specific positive drivers flagged.</p>
            )}
          </div>

          {/* Risk Factors */}
          <div className="p-3.5 rounded-xl bg-rose-950/10 border border-rose-500/20 space-y-2">
            <h4 className="font-bold text-rose-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              Forecast Risk Factors
            </h4>
            {forecast.confidence_factors.negative_factors.length > 0 ? (
              <ul className="space-y-1 text-slate-300 text-[11px] leading-relaxed">
                {forecast.confidence_factors.negative_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-rose-400 font-bold">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500 text-[11px]">No significant risk factors flagged.</p>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
