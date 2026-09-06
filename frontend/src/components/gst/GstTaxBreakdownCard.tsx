import React from 'react';
import { GSTTaxCalculationResponse } from '../../services/gstApi';
import { MapPin, Receipt } from 'lucide-react';

interface GstTaxBreakdownCardProps {
  gstData: GSTTaxCalculationResponse | null;
  loading?: boolean;
}

export const GstTaxBreakdownCard: React.FC<GstTaxBreakdownCardProps> = ({ gstData, loading }) => {
  if (loading) {
    return (
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl animate-pulse space-y-3">
        <div className="h-4 bg-slate-800 rounded w-1/3"></div>
        <div className="h-8 bg-slate-800/50 rounded"></div>
      </div>
    );
  }

  if (!gstData) return null;

  const isIntra = gstData.is_intra_state;

  return (
    <div className="p-5 bg-slate-900/70 border border-slate-800 rounded-2xl space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Receipt className="w-5 h-5 text-indigo-400" />
          <h4 className="text-xs font-bold font-mono text-white uppercase tracking-wider">
            🇮🇳 GST & HSN Regulatory Tax Breakdown Engine
          </h4>
        </div>
        <span
          className={`px-2.5 py-0.5 text-[10px] font-bold rounded-full border flex items-center gap-1 font-mono ${
            isIntra
              ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
              : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
          }`}
        >
          <MapPin className="w-3 h-3" />
          {isIntra ? 'Intra-State (CGST + SGST)' : 'Inter-State (IGST)'}
        </span>
      </div>

      {/* State Matching Bar */}
      <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Origin State:</span>
          <strong className="text-white">{gstData.seller_state} (Code {gstData.seller_state_code})</strong>
        </div>
        <span className="text-slate-600">➔</span>
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Destination State:</span>
          <strong className="text-white">{gstData.buyer_state} (Code {gstData.buyer_state_code})</strong>
        </div>
      </div>

      {/* Financial Split Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 block uppercase">Taxable Value</span>
          <span className="text-sm font-bold font-mono text-white">
            ₹{parseFloat(gstData.total_taxable_value).toLocaleString('en-IN')}
          </span>
        </div>

        {isIntra ? (
          <>
            <div className="p-3 bg-indigo-950/30 border border-indigo-800/40 rounded-xl">
              <span className="text-[10px] font-semibold text-indigo-400 block uppercase">CGST Amount</span>
              <span className="text-sm font-bold font-mono text-indigo-300">
                ₹{parseFloat(gstData.total_cgst_amount).toLocaleString('en-IN')}
              </span>
            </div>
            <div className="p-3 bg-indigo-950/30 border border-indigo-800/40 rounded-xl">
              <span className="text-[10px] font-semibold text-indigo-400 block uppercase">SGST Amount</span>
              <span className="text-sm font-bold font-mono text-indigo-300">
                ₹{parseFloat(gstData.total_sgst_amount).toLocaleString('en-IN')}
              </span>
            </div>
          </>
        ) : (
          <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl col-span-2">
            <span className="text-[10px] font-semibold text-emerald-400 block uppercase">IGST Amount</span>
            <span className="text-sm font-bold font-mono text-emerald-300">
              ₹{parseFloat(gstData.total_igst_amount).toLocaleString('en-IN')}
            </span>
          </div>
        )}

        <div className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 block uppercase">Grand Total (Incl Tax)</span>
          <span className="text-sm font-bold font-mono text-white">
            ₹{parseFloat(gstData.grand_total).toLocaleString('en-IN')}
          </span>
        </div>
      </div>

      {/* Item-level HSN breakdown list */}
      {gstData.items && gstData.items.length > 0 && (
        <div className="space-y-1.5 pt-2">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Line HSN Summary</span>
          <div className="space-y-1 max-h-36 overflow-y-auto">
            {gstData.items.map((item) => (
              <div key={item.item_index} className="flex items-center justify-between p-2 bg-slate-950/60 rounded-lg text-xs font-mono border border-slate-800/60">
                <span className="text-slate-300 truncate max-w-[200px]">{item.product_name}</span>
                <span className="px-2 py-0.5 bg-slate-800 text-indigo-300 text-[10px] font-bold rounded">HSN: {item.hsn_sac_code}</span>
                <span className="text-slate-400">Rate: {item.gst_rate}%</span>
                <span className="text-emerald-400 font-bold">₹{parseFloat(item.total_line_tax).toLocaleString('en-IN')} Tax</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
