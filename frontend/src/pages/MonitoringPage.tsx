import React, { useEffect, useState } from 'react';
import { ShieldAlert, Clock, TrendingUp, Truck, RefreshCw, Sparkles } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { intelligenceApi } from '../services/intelligenceApi';
import { StalledQuotesResponse, DiscountAnomaliesResponse, DeliverySlippageResponse, NudgesResponse } from '../types';
import { NudgesDrawer } from '../components/intelligence/NudgesDrawer';

export const MonitoringPage: React.FC = () => {
  const [stalledData, setStalledData] = useState<StalledQuotesResponse | null>(null);
  const [discountData, setDiscountData] = useState<DiscountAnomaliesResponse | null>(null);
  const [deliveryData, setDeliveryData] = useState<DeliverySlippageResponse | null>(null);
  const [nudgesData, setNudgesData] = useState<NudgesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isNudgesOpen, setIsNudgesOpen] = useState(false);

  const fetchMonitoringData = async () => {
    setLoading(true);
    try {
      const [stalled, discounts, delivery, nudges] = await Promise.all([
        intelligenceApi.getStalledQuotes(),
        intelligenceApi.getDiscountAnomalies(),
        intelligenceApi.getDeliverySlippage(),
        intelligenceApi.getNudges(),
      ]);
      setStalledData(stalled);
      setDiscountData(discounts);
      setDeliveryData(delivery);
      setNudgesData(nudges);
    } catch (err) {
      console.error('Failed to fetch monitoring telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            <ShieldAlert className="w-7 h-7 text-indigo-400" />
            Commercial & Fulfillment Telemetry
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Phases 54–57: Stalled Quotes, Discount Anomalies, Delivery Slippage & Automated Nudges
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsNudgesOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-xs shadow-lg shadow-indigo-500/25 transition"
          >
            <Sparkles className="w-4 h-4" />
            <span>Nudges Drawer ({nudgesData?.open_count || 0})</span>
          </button>

          <button
            onClick={fetchMonitoringData}
            disabled={loading}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Stalled Quotations</span>
            <Clock className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-white mt-2">
            {stalledData?.total_stalled_count || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Sent quotes inactive &gt; 14 days</p>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Discount Anomalies</span>
            <TrendingUp className="w-5 h-5 text-rose-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-white mt-2">
            {discountData?.anomalous_count || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Variance above customer/org baseline</p>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Delivery Slippages</span>
            <Truck className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-white mt-2 flex items-baseline gap-2">
            <span>{(deliveryData?.at_risk_count || 0) + (deliveryData?.delayed_count || 0)}</span>
            <span className="text-xs text-rose-400 font-normal">({deliveryData?.delayed_count || 0} delayed)</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Promised delivery vs expected fulfillment</p>
        </GlassCard>
      </div>

      {/* Grid of Monitoring Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Phase 54: Stalled Quotes */}
        <GlassCard className="p-5 lg:col-span-1 border border-white/10">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" />
            Phase 54 — Stalled Quotes
          </h3>
          {stalledData?.stalled_quotes.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No stalled quotations detected.</p>
          ) : (
            <div className="space-y-3">
              {stalledData?.stalled_quotes.map((q) => (
                <div key={q.quotation_id} className="p-3 rounded-lg bg-black/20 border border-white/10 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-200">{q.quotation_number}</span>
                    <span className="text-rose-400 font-mono font-semibold">{q.days_inactive}d stalled</span>
                  </div>
                  <div className="text-slate-300 font-medium">{q.customer_name}</div>
                  <p className="text-[11px] text-slate-400 mt-1">{q.stall_reason}</p>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Phase 55: Discount Anomalies */}
        <GlassCard className="p-5 lg:col-span-1 border border-white/10">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-rose-400" />
            Phase 55 — Discount Anomalies
          </h3>
          {discountData?.anomalies.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No commercial discount anomalies detected.</p>
          ) : (
            <div className="space-y-3">
              {discountData?.anomalies.map((da) => (
                <div key={da.quotation_id} className="p-3 rounded-lg bg-black/20 border border-white/10 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-200">{da.quotation_number}</span>
                    <span className="text-amber-300 font-mono font-bold">{da.blended_discount_percent}%</span>
                  </div>
                  <div className="text-slate-300 font-medium">{da.customer_name}</div>
                  <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
                    <span>Baseline: {da.organization_avg_discount}%</span>
                    <span className="text-rose-400 font-semibold">+{da.variance_percent}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Phase 56: Delivery Slippage */}
        <GlassCard className="p-5 lg:col-span-1 border border-white/10">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
            <Truck className="w-4 h-4 text-indigo-400" />
            Phase 56 — Delivery Slippage
          </h3>
          {deliveryData?.deliveries.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">All deliveries on track.</p>
          ) : (
            <div className="space-y-3">
              {deliveryData?.deliveries.map((ds) => (
                <div key={ds.delivery_promise_id} className="p-3 rounded-lg bg-black/20 border border-white/10 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-200">{ds.quotation_number}</span>
                    <StatusBadge status={ds.status} variant={ds.status === 'DELAYED' ? 'danger' : 'warning'} />
                  </div>
                  <div className="text-slate-300 font-medium">{ds.customer_name}</div>
                  <p className="text-[11px] text-slate-400 mt-1">{ds.root_cause}</p>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Drawer */}
      <NudgesDrawer
        isOpen={isNudgesOpen}
        onClose={() => setIsNudgesOpen(false)}
        nudgesData={nudgesData}
        onRefresh={fetchMonitoringData}
      />
    </div>
  );
};
