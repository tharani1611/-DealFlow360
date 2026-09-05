import React, { useEffect, useState } from 'react';
import { BarChart3, PieChart, DollarSign, RefreshCw, Calendar, CheckCircle2, ShoppingBag, ShieldCheck } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { intelligenceApi } from '../services/intelligenceApi';
import { ExecutiveReportSummaryResponse, ExecutiveAnalyticsResponse } from '../types';

export const ReportsPage: React.FC = () => {
  const [period, setPeriod] = useState<string>('this_month');
  const [report, setReport] = useState<ExecutiveReportSummaryResponse | null>(null);
  const [analytics, setAnalytics] = useState<ExecutiveAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReportsData = async () => {
    setLoading(true);
    try {
      const [reportResp, analyticsResp] = await Promise.all([
        intelligenceApi.getExecutiveReport(period),
        intelligenceApi.getExecutiveAnalytics(period),
      ]);
      setReport(reportResp);
      setAnalytics(analyticsResp);
    } catch (err) {
      console.error('Failed to fetch reporting analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportsData();
  }, [period]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-indigo-400" />
            Executive Reporting & Financial Analytics
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Phases 58 & 59: 100% Server-Side Decimal Precision Engine
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300">
            <Calendar className="w-4 h-4 text-indigo-400" />
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-transparent text-white focus:outline-none cursor-pointer"
            >
              <option value="this_month" className="bg-slate-900">This Month</option>
              <option value="last_month" className="bg-slate-900">Last Month</option>
              <option value="this_quarter" className="bg-slate-900">This Quarter</option>
              <option value="this_year" className="bg-slate-900">This Year</option>
            </select>
          </div>

          <button
            onClick={fetchReportsData}
            disabled={loading}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Precision Badge */}
      <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0" />
          <span>
            <strong>100% Server-Side Decimal Precision Engine:</strong> Financial aggregations computed with exact PostgreSQL & Python Decimal arithmetic.
          </span>
        </div>
        {analytics?.monitoring_summary && (
          <div className="flex items-center gap-3 text-[11px] font-mono shrink-0">
            <span className="px-2 py-0.5 rounded bg-black/30 border border-white/10 text-amber-300">
              {analytics.monitoring_summary.stalled_quotes_count} Stalled
            </span>
            <span className="px-2 py-0.5 rounded bg-black/30 border border-white/10 text-rose-300">
              {analytics.monitoring_summary.discount_anomalies_count} Anomalies
            </span>
            <span className="px-2 py-0.5 rounded bg-black/30 border border-white/10 text-indigo-300">
              {analytics.monitoring_summary.open_nudges_count} Open Nudges
            </span>
          </div>
        )}
      </div>

      {/* Report Summary Cards Grid */}
      {loading || !report ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          <div className="h-48 bg-white/5 rounded-xl"></div>
          <div className="h-48 bg-white/5 rounded-xl"></div>
          <div className="h-48 bg-white/5 rounded-xl"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Sales Domain */}
          <GlassCard className="p-5 border border-white/10">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center justify-between">
              <span>Sales Pipeline</span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Pipeline Total Value</span>
                <span className="font-mono font-bold text-white">${report.sales.pipeline_total_value}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Won Revenue</span>
                <span className="font-mono font-bold text-emerald-400">${report.sales.won_revenue}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Deals Won / Open</span>
                <span className="font-mono text-slate-200">{report.sales.won_deals_count} / {report.sales.open_deals_count}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-white/10">
                <span className="text-slate-400 font-semibold">Win Rate</span>
                <span className="font-mono font-extrabold text-emerald-400">{report.sales.win_rate_percent}%</span>
              </div>
            </div>
          </GlassCard>

          {/* Quotations Domain */}
          <GlassCard className="p-5 border border-white/10">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center justify-between">
              <span>Quotation Conversions</span>
              <PieChart className="w-4 h-4 text-cyan-400" />
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Total Quotations</span>
                <span className="font-mono font-bold text-white">{report.quotations.total_quotations_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Accepted Quotes</span>
                <span className="font-mono font-bold text-cyan-400">{report.quotations.accepted_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Average Quote Value</span>
                <span className="font-mono text-slate-200">${report.quotations.average_quotation_value}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-white/10">
                <span className="text-slate-400 font-semibold">Conversion Rate</span>
                <span className="font-mono font-extrabold text-cyan-400">{report.quotations.conversion_rate_percent}%</span>
              </div>
            </div>
          </GlassCard>

          {/* Commercial Domain */}
          <GlassCard className="p-5 border border-white/10">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center justify-between">
              <span>Commercial Margins</span>
              <ShoppingBag className="w-4 h-4 text-indigo-400" />
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Gross Revenue</span>
                <span className="font-mono font-bold text-white">${report.commercial.gross_revenue}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Gross Margin</span>
                <span className="font-mono font-bold text-indigo-300">${report.commercial.gross_margin}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Total Discounts Given</span>
                <span className="font-mono text-amber-300">${report.commercial.total_discounts_given}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-white/10">
                <span className="text-slate-400 font-semibold">Gross Margin %</span>
                <span className="font-mono font-extrabold text-indigo-400">{report.commercial.gross_margin_percent}%</span>
              </div>
            </div>
          </GlassCard>

          {/* Subscriptions Domain */}
          <GlassCard className="p-5 border border-white/10">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center justify-between">
              <span>Subscription Engine (ARR/MRR)</span>
              <BarChart3 className="w-4 h-4 text-emerald-400" />
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Active Subscriptions</span>
                <span className="font-mono font-bold text-white">{report.subscriptions.active_subscriptions_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Monthly Recurring (MRR)</span>
                <span className="font-mono font-bold text-emerald-400">${report.subscriptions.monthly_recurring_revenue}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Annualized Recurring (ARR)</span>
                <span className="font-mono font-bold text-emerald-300">${report.subscriptions.annual_recurring_revenue}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-white/10">
                <span className="text-slate-400 font-semibold">Churn Rate</span>
                <span className="font-mono font-extrabold text-slate-300">{report.subscriptions.churn_rate_percent}%</span>
              </div>
            </div>
          </GlassCard>

          {/* Fulfillment Domain */}
          <GlassCard className="p-5 border border-white/10 md:col-span-2 lg:col-span-2">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center justify-between">
              <span>Fulfillment & Delivery Performance</span>
              <CheckCircle2 className="w-4 h-4 text-violet-400" />
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div className="p-3 rounded-lg bg-black/20 border border-white/5">
                <div className="text-slate-400">Total Deliveries</div>
                <div className="text-lg font-mono font-bold text-white mt-1">{report.fulfillment.total_deliveries}</div>
              </div>
              <div className="p-3 rounded-lg bg-black/20 border border-white/5">
                <div className="text-slate-400">On-Time Delivery %</div>
                <div className="text-lg font-mono font-bold text-emerald-400 mt-1">{report.fulfillment.on_time_delivery_percent}%</div>
              </div>
              <div className="p-3 rounded-lg bg-black/20 border border-white/5">
                <div className="text-slate-400">At Risk / Delayed</div>
                <div className="text-lg font-mono font-bold text-rose-400 mt-1">{report.fulfillment.at_risk_count} / {report.fulfillment.delayed_count}</div>
              </div>
              <div className="p-3 rounded-lg bg-black/20 border border-white/5">
                <div className="text-slate-400">Avg Slippage Days</div>
                <div className="text-lg font-mono font-bold text-slate-200 mt-1">{report.fulfillment.average_slippage_days} days</div>
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
};
