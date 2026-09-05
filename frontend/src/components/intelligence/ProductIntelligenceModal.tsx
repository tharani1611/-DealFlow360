import React, { useEffect, useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { Product360Intelligence } from '../../types';
import { intelligenceApi } from '../../services/intelligenceApi';
import { LoadingState, ErrorState } from '../ui/EmptyState';
import { Sparkles } from 'lucide-react';

interface ProductIntelligenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  productId: string | null;
}

export const ProductIntelligenceModal: React.FC<ProductIntelligenceModalProps> = ({
  isOpen,
  onClose,
  productId,
}) => {
  const [data, setData] = useState<Product360Intelligence | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !productId) return;
    setIsLoading(true);
    setError(null);

    intelligenceApi
      .getProduct360(productId)
      .then((res) => setData(res))
      .catch((err) => setError(err.message || 'Failed to load Product Intelligence 360.'))
      .finally(() => setIsLoading(false));
  }, [isOpen, productId]);

  if (!isOpen || !productId) return null;

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Product Intelligence 360 — ${data?.name || 'Loading...'}`}
      maxWidth="2xl"
    >
      {isLoading ? (
        <LoadingState message="Calculating product performance, margin %, penetration rate, and co-purchase affinity matrix..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : data ? (
        <div className="space-y-6 font-mono text-xs">
          {/* Header KPI Banner */}
          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <span className="text-[10px] text-indigo-400 font-bold uppercase block tracking-wider">SKU: {data.sku}</span>
              <h3 className="text-lg font-black text-slate-100 mt-0.5">{data.name}</h3>
              <p className="text-[11px] text-slate-400 font-sans mt-0.5">{data.description || 'No description provided.'}</p>
            </div>

            <div className="flex items-center gap-3 text-right">
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">Unit Selling Price</span>
                <span className="text-base font-black text-emerald-400">${data.unit_price}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase block">Popularity Rank</span>
                <span className="text-base font-black text-indigo-300">#{data.performance.popularity_rank}</span>
              </div>
            </div>
          </div>

          {/* Performance Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] p-4 bg-slate-950/60 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Revenue</span>
              <span className="font-black text-slate-100 text-sm mt-0.5 block">${data.performance.total_revenue}</span>
              <span className="text-[10px] text-slate-500 block">{data.performance.units_won} units sold</span>
            </div>

            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Gross Margin %</span>
              <span className={`font-black text-sm mt-0.5 block ${
                data.performance.margin_percentage >= 50
                  ? 'text-emerald-400'
                  : data.performance.margin_percentage >= 30
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}>
                {data.performance.margin_percentage}%
              </span>
              <span className="text-[10px] text-slate-500 block">${data.performance.gross_margin} profit</span>
            </div>

            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Win Rate %</span>
              <span className="font-black text-cyan-300 text-sm mt-0.5 block">{data.performance.win_rate_percent}%</span>
              <span className="text-[10px] text-slate-500 block">{data.performance.won_deal_count}/{data.performance.deal_count} deals</span>
            </div>

            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Customer Penetration</span>
              <span className="font-black text-indigo-300 text-sm mt-0.5 block">{data.performance.penetration_rate_percent}%</span>
              <span className="text-[10px] text-slate-500 block">{data.performance.customer_count} active accounts</span>
            </div>
          </div>

          {/* AI Advisory Summary */}
          {data.ai_explanation && (
            <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-indigo-300 space-y-1">
              <span className="font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5 text-indigo-400">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                AI Product Sales Intelligence Advisory
              </span>
              <p className="text-[11px] font-sans leading-relaxed">{data.ai_explanation}</p>
            </div>
          )}

          {/* Co-Purchase Affinity Matrix Table */}
          <div className="space-y-2">
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px] block">
              Observed Co-Purchase Affinity Relationships ({data.affinities.length})
            </span>

            {data.affinities.length > 0 ? (
              <div className="space-y-2">
                {data.affinities.map((aff, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between gap-3 text-[11px]"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100">{aff.target_product_name}</span>
                        <span className="text-[10px] text-indigo-400 font-bold">[{aff.target_sku}]</span>
                      </div>
                      <span className="text-[10px] text-slate-400 block mt-0.5">
                        Co-purchased in {aff.co_purchase_count} deal(s) • {aff.attachment_rate_percent}% attachment rate
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-right">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                        aff.relationship_type === 'UPSELL'
                          ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                          : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                      }`}>
                        {aff.relationship_type}
                      </span>
                      <span className="font-bold text-emerald-400">${aff.unit_price}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-slate-950/40 rounded-xl border border-slate-800/60 text-center text-slate-500 text-xs">
                No co-purchase product affinity observed yet in historical quotations.
              </div>
            )}
          </div>
        </div>
      ) : null}
    </GlassModal>
  );
};
