import React from 'react';
import { CustomerHealthDetail } from '../../types';
import { GlassCard } from '../ui/GlassCard';
import { ShieldCheck, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface CustomerHealthCardProps {
  health: CustomerHealthDetail;
  customerName: string;
}

export const CustomerHealthCard: React.FC<CustomerHealthCardProps> = ({ health, customerName }) => {
  const isHealthy = health.health_category === 'HEALTHY' || health.health_category === 'ENGAGED';
  const isAtRisk = health.health_category === 'AT_RISK' || health.health_category === 'INACTIVE';

  return (
    <GlassCard
      title={
        <div className="flex items-center justify-between font-mono">
          <span className="flex items-center gap-2 text-slate-100 text-base">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            Customer Health & Segment Intelligence
          </span>

          <div className="flex items-center gap-2 text-xs">
            <span className={`px-2.5 py-0.5 rounded-md font-bold uppercase border ${
              isHealthy
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : isAtRisk
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
            }`}>
              {health.health_category}
            </span>

            <span className="px-2.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-bold uppercase border border-indigo-500/40">
              {health.segment}
            </span>
          </div>
        </div>
      }
      subtitle={`Deterministic telemetry analysis for ${customerName}`}
    >
      <div className="space-y-6 font-mono text-xs">
        {/* KPI Score Banner */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 bg-slate-950/80 rounded-xl border border-slate-800 gap-4">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Deterministic Health Score</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-4xl font-black ${
                health.health_score >= 80
                  ? 'text-emerald-400'
                  : health.health_score >= 50
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}>
                {health.health_score}
              </span>
              <span className="text-xs text-slate-500 font-bold">/ 100</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-right">
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Account Segment</span>
              <span className="font-extrabold text-indigo-300 text-sm">{health.segment}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Lifecycle Stage</span>
              <span className="font-extrabold text-cyan-300 text-sm">{health.lifecycle_stage}</span>
            </div>
          </div>
        </div>

        {/* Drivers Breakdown Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Positive Drivers */}
          <div className="p-4 bg-emerald-950/20 border border-emerald-500/30 rounded-xl space-y-2">
            <span className="text-[11px] font-bold text-emerald-400 uppercase flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Positive Health Drivers ({health.positive_drivers.length})
            </span>

            {health.positive_drivers.length > 0 ? (
              <ul className="space-y-1.5 text-[11px] text-slate-300">
                {health.positive_drivers.map((driver, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">+</span>
                    <span>{driver}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-slate-500 italic">No specific positive drivers recorded.</p>
            )}
          </div>

          {/* Negative Risk Drivers */}
          <div className="p-4 bg-rose-950/20 border border-rose-500/30 rounded-xl space-y-2">
            <span className="text-[11px] font-bold text-rose-400 uppercase flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              Risk Drivers & Friction Points ({health.negative_drivers.length})
            </span>

            {health.negative_drivers.length > 0 ? (
              <ul className="space-y-1.5 text-[11px] text-slate-300">
                {health.negative_drivers.map((risk, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold">-</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-emerald-400 font-bold">✓ Zero active risk factors detected.</p>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
