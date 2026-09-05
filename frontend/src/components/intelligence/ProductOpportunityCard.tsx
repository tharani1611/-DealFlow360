import React from 'react';
import { ArrowUpRight, Plus, CheckCircle2 } from 'lucide-react';
import { ProductRecommendationItem } from '../../types';
import { GlassCard } from '../ui/GlassCard';
import { BrutalButton } from '../ui/BrutalButton';

interface ProductOpportunityCardProps {
  recommendation: ProductRecommendationItem;
  onCreateActivity?: (rec: ProductRecommendationItem) => void;
}

export const ProductOpportunityCard: React.FC<ProductOpportunityCardProps> = ({
  recommendation,
  onCreateActivity,
}) => {
  const isUpsell = recommendation.recommendation_type === 'upsell';

  return (
    <GlassCard className={`p-4 backdrop-blur-md border border-slate-800 transition hover:border-slate-700 ${
      isUpsell ? 'border-l-4 border-l-emerald-500 bg-emerald-950/10' : 'border-l-4 border-l-indigo-500 bg-indigo-950/10'
    }`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          {/* Header Row & Badges */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="font-extrabold text-slate-100 text-sm">{recommendation.product_name}</span>

            {isUpsell ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                <ArrowUpRight className="w-3 h-3" /> UPSELL
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 flex items-center gap-1">
                <Plus className="w-3 h-3" /> CROSS-SELL
              </span>
            )}

            <span className="text-[10px] font-mono text-slate-400 font-bold">
              SKU: {recommendation.sku}
            </span>
          </div>

          {/* Context Line */}
          <p className="text-xs text-slate-300 font-mono leading-relaxed mt-1">
            {recommendation.reason}
          </p>

          {/* Eligibility Note */}
          {recommendation.eligibility && (
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 mt-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>{recommendation.eligibility}</span>
            </div>
          )}
        </div>

        {/* Pricing & Action */}
        <div className="shrink-0 text-right space-y-2 font-mono">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Target Price</span>
            <span className="text-sm font-extrabold text-slate-100">${Number(recommendation.unit_price).toLocaleString()}</span>
          </div>

          {onCreateActivity && (
            <BrutalButton
              variant={isUpsell ? 'success' : 'primary'}
              size="sm"
              icon={Plus}
              onClick={() => onCreateActivity(recommendation)}
              className="text-xs py-1"
            >
              Create Activity
            </BrutalButton>
          )}
        </div>
      </div>
    </GlassCard>
  );
};
