import React from 'react';
import { NeoGlassCard } from '../ui/NeoGlassCard';
import { StatusBadge } from '../ui/StatusBadge';
import { BillingClassification } from '../../types';
import { CreditCard, Repeat, Layers } from 'lucide-react';

interface HybridBillingSummaryCardProps {
  billing: BillingClassification | null;
  currency?: string;
  isLoading?: boolean;
}

export const HybridBillingSummaryCard: React.FC<HybridBillingSummaryCardProps> = ({
  billing,
  currency = 'USD',
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <NeoGlassCard className="p-4 animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/3 mb-2"></div>
        <div className="h-8 bg-slate-800 rounded w-1/2"></div>
      </NeoGlassCard>
    );
  }

  if (!billing) {
    return null;
  }

  const modelColor =
    billing.commercial_model === 'HYBRID'
      ? 'purple'
      : billing.commercial_model === 'RECURRING'
      ? 'info'
      : 'success';

  return (
    <NeoGlassCard className="p-5 border-l-4 border-l-purple-500">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-purple-400" />
          <h3 className="text-base font-bold text-slate-100">Hybrid Commercial Billing</h3>
        </div>
        <StatusBadge status={billing.commercial_model} variant={modelColor} size="md" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-sky-950/60 border border-sky-500/30 text-sky-400">
            <CreditCard className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">One-Time Physical Goods</div>
            <div className="text-lg font-black font-mono text-sky-300">
              {currency} {Number(billing.one_time_total).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-purple-950/60 border border-purple-500/30 text-purple-400">
            <Repeat className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Recurring Monthly MRR</div>
            <div className="text-lg font-black font-mono text-purple-300">
              {currency} {Number(billing.recurring_monthly_total).toLocaleString('en-US', { minimumFractionDigits: 2 })} / mo
            </div>
          </div>
        </div>
      </div>

      {billing.line_classifications && billing.line_classifications.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">Line Item Classification Breakdown</div>
          <div className="divide-y divide-slate-800/60 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40">
            {billing.line_classifications.map((item, idx) => (
              <div key={idx} className="p-2.5 flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-1.5 py-0.5 text-[9px] font-bold rounded uppercase ${
                      item.billing_type === 'RECURRING'
                        ? 'bg-purple-950/80 text-purple-300 border border-purple-500/30'
                        : 'bg-sky-950/80 text-sky-300 border border-sky-500/30'
                    }`}
                  >
                    {item.billing_type}
                  </span>
                  <span className="text-slate-200 font-sans font-medium">{item.product_name}</span>
                </div>
                <div className="text-slate-300 font-bold">
                  {currency} {Number(item.line_total).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </NeoGlassCard>
  );
};
