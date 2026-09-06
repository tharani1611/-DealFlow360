import React from 'react';
import { GlassModal } from '../ui/GlassModal';
import { Product } from '../../types';
import { Tag, ShieldCheck, Layers } from 'lucide-react';

interface PricingRulesBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}

export const PricingRulesBreakdownModal: React.FC<PricingRulesBreakdownModalProps> = ({
  isOpen,
  onClose,
  product,
}) => {
  if (!product) return null;

  const basePrice = Number(product.unit_price || 0);

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title={`Pricing Telemetry & Rules — ${product.name}`}>
      <div className="space-y-4 text-xs">
        {/* Base Unit Price Card */}
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex justify-between items-center">
          <div>
            <div className="text-slate-400 font-mono text-[11px] uppercase">Base Unit Price</div>
            <div className="text-2xl font-black text-white font-mono mt-0.5">₹{basePrice.toFixed(2)} {product.currency}</div>
          </div>
          <Tag className="w-8 h-8 text-indigo-400 opacity-80" />
        </div>

        {/* Volume Tier Pricing Rules Matrix */}
        <div>
          <div className="font-bold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-cyan-400" />
            Automated Quantity Tier Breakdown
          </div>

          <div className="space-y-2">
            <div className="p-3 rounded-lg bg-black/20 border border-white/10 flex justify-between items-center">
              <div>
                <span className="font-bold text-slate-200">Tier 1 (Standard): 1–10 units</span>
                <p className="text-[11px] text-slate-400">List price — 0% discount</p>
              </div>
              <span className="font-mono font-bold text-white">₹{basePrice.toFixed(2)}</span>
            </div>

            <div className="p-3 rounded-lg bg-black/20 border border-white/10 flex justify-between items-center">
              <div>
                <span className="font-bold text-slate-200">Tier 2 (Volume): 11–50 units</span>
                <p className="text-[11px] text-emerald-400">5.0% volume discount applied</p>
              </div>
              <span className="font-mono font-bold text-emerald-300">${(basePrice * 0.95).toFixed(2)}</span>
            </div>

            <div className="p-3 rounded-lg bg-black/20 border border-white/10 flex justify-between items-center">
              <div>
                <span className="font-bold text-slate-200">Tier 3 (Enterprise): 51+ units</span>
                <p className="text-[11px] text-emerald-400">10.0% volume discount applied</p>
              </div>
              <span className="font-mono font-bold text-emerald-300">${(basePrice * 0.90).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Commercial Governance Rules Header */}
        <div className="pt-2 border-t border-white/10 text-[11px] text-slate-400 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Backend-authoritative pricing rules enforced on all quotation creation.</span>
        </div>
      </div>
    </GlassModal>
  );
};
