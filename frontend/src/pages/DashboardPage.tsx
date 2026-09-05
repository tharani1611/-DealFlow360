import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { dealApi } from '../services/dealApi';
import { aiApi } from '../services/aiApi';
import { intelligenceApi } from '../services/intelligenceApi';
import { forecastApi } from '../services/forecastApi';
import { Deal, AssistantResponse, DashboardIntelligenceResponse, AttentionCenterResponse, RevenueForecastResponse } from '../types';
import { MetricCard } from '../components/ui/MetricCard';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { AttentionCenterWidget } from '../components/intelligence/AttentionCenterWidget';
import { RevenueForecastCard } from '../components/intelligence/RevenueForecastCard';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import {
  TrendingUp,
  Briefcase,
  ArrowRight,
  Plus,
  ShieldAlert,
  Flame,
  Activity as ActivityIcon,
  AlertTriangle,
  PieChart,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [deals, setDeals] = useState<Deal[]>([]);
  const [aiAnswer, setAiAnswer] = useState<AssistantResponse | null>(null);
  const [intel, setIntel] = useState<DashboardIntelligenceResponse | null>(null);
  const [attentionData, setAttentionData] = useState<AttentionCenterResponse | null>(null);
  const [forecast, setForecast] = useState<RevenueForecastResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queryText, setQueryText] = useState('Which deals need follow-up this week?');

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dealsData, intelData, attData, fcData] = await Promise.all([
        dealApi.getDeals({ limit: 10 }),
        intelligenceApi.getDashboardIntelligence().catch(() => null),
        intelligenceApi.getAttention().catch(() => null),
        forecastApi.getForecast().catch(() => null),
      ]);
      setDeals(dealsData);
      setIntel(intelData);
      setAttentionData(attData);
      setForecast(fcData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard operational data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleAskAi = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!queryText.trim()) return;
    setIsAiLoading(true);
    try {
      const res = await aiApi.askAssistant(queryText.trim());
      setAiAnswer(res);
    } catch {
      // Fallback
    } finally {
      setIsAiLoading(false);
    }
  };

  if (isLoading) return <LoadingState message="Connecting to CRM Command Telemetry..." />;
  if (error) return <ErrorState message={error} onRetry={loadDashboardData} />;

  // Calculated Metrics fallback
  const pipelineValue = deals.reduce((sum, d) => sum + Number(d.value || 0), 0);
  const activeDealsCount = deals.filter((d) => d.status === 'open').length;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 backdrop-blur-glass border border-slate-700/80 rounded-2xl p-6 shadow-neo border-t-2 border-t-indigo-500">
        <div>
          <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest flex items-center gap-1.5">
            <ActivityIcon className="w-3.5 h-3.5 text-indigo-400" />
            OPERATIONAL INTELLIGENCE COMMAND CENTER
          </span>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight mt-0.5">
            Welcome back, {user?.full_name || 'System Operator'}
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time pipeline value, weighted forecasts, deal health telemetry, and customer cooling alerts
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <BrutalButton variant="secondary" icon={Plus} onClick={() => navigate('/customers')}>
            Add Customer
          </BrutalButton>
          <BrutalButton variant="primary" icon={Plus} onClick={() => navigate('/deals')}>
            New Deal
          </BrutalButton>
        </div>
      </div>

      {/* Pipeline Concentration Risk Warning Banner */}
      {intel?.pipeline?.concentration?.is_concentrated && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 backdrop-blur-md">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5 animate-pulse" />
          <div className="text-xs">
            <h4 className="font-extrabold text-amber-300 font-mono uppercase tracking-wider">
              PIPELINE CONCENTRATION RISK DETECTED
            </h4>
            <p className="text-slate-300 mt-0.5">
              {intel.pipeline.concentration.recommendation ||
                'A high percentage of open pipeline value is concentrated in top opportunities.'}
            </p>
          </div>
        </div>
      )}

      {/* KPI Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          label="Open Pipeline Value"
          value={intel?.pipeline?.open_pipeline_value ? `$${Number(intel.pipeline.open_pipeline_value).toLocaleString()}` : `$${pipelineValue.toLocaleString()}`}
          subtitle={`${activeDealsCount} open deal opportunities`}
          icon={TrendingUp}
          variant="primary"
        />
        <MetricCard
          label="Weighted Forecast"
          value={intel?.pipeline?.weighted_pipeline_value ? `$${Number(intel.pipeline.weighted_pipeline_value).toLocaleString()}` : `$${(pipelineValue * 0.5).toLocaleString()}`}
          subtitle={intel?.pipeline?.forecast_confidence_label || "Weighted win probability"}
          icon={Briefcase}
          variant="accent"
        />
        <MetricCard
          label="Deals at Risk"
          value={intel?.deals_at_risk?.length ?? 0}
          subtitle="Deals with health score < 60"
          icon={ShieldAlert}
          variant="warning"
        />
        <MetricCard
          label="Customers Going Cold"
          value={intel?.customers_going_cold?.length ?? 0}
          subtitle="Relationship engagement declining"
          icon={Flame}
          variant="danger"
        />
      </div>

      {/* Revenue Forecast Widget */}
      {forecast && <RevenueForecastCard forecast={forecast} />}

      {/* Executive Sales Attention Center */}
      <AttentionCenterWidget attentionData={attentionData} />

      {/* Pipeline Stage Distribution breakdown visualizer */}
      {intel?.pipeline?.stage_breakdown && intel.pipeline.stage_breakdown.length > 0 && (
        <GlassCard
          title={
            <div className="flex items-center gap-2 text-indigo-300">
              <PieChart className="w-5 h-5 text-indigo-400" />
              <span>Pipeline Stage Breakdown & Concentration Analytics</span>
            </div>
          }
          subtitle="Distribution of open deal values across pipeline lifecycle stages"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {intel.pipeline.stage_breakdown.map((item) => (
              <div
                key={item.stage}
                className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-xs space-y-1 hover:border-indigo-500/30 transition"
              >
                <div className="flex justify-between items-center text-[11px] font-mono text-slate-400 capitalize">
                  <span className="truncate">{item.stage.replace('_', ' ')}</span>
                  <span className="font-bold text-indigo-400">{item.count} deals</span>
                </div>
                <div className="text-base font-extrabold text-slate-100 font-mono">
                  ${Number(item.total_value || 0).toLocaleString()}
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(10, item.count * 20))}%` }}
                  />
                </div>
                <div className="text-[10px] text-slate-500 font-mono text-right">Weighted: ${Number(item.weighted_value || 0).toLocaleString()}</div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 spans) - Deals at Risk & Pipeline Opportunities */}
        <div className="lg:col-span-2 space-y-8">
          {/* Deals at Risk Intelligence Card */}
          {intel && intel.deals_at_risk.length > 0 && (
            <GlassCard
              title={
                <span className="flex items-center gap-2 text-rose-300">
                  <ShieldAlert className="w-5 h-5 text-rose-400" />
                  Deals Requiring Attention & Health Recovery
                </span>
              }
              subtitle="Opportunities with elevated execution or engagement risk"
              action={
                <BrutalButton variant="ghost" size="sm" icon={ArrowRight} onClick={() => navigate('/deals')}>
                  View Pipeline
                </BrutalButton>
              }
            >
              <div className="divide-y divide-slate-800">
                {intel.deals_at_risk.map((item) => (
                  <div
                    key={item.deal_id}
                    onClick={() => navigate(`/deals/${item.deal_id}`)}
                    className="py-3 flex items-center justify-between gap-4 hover:bg-slate-800/40 px-3 rounded-xl transition cursor-pointer group"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100 text-sm group-hover:text-indigo-300 transition">
                          {item.title}
                        </span>
                        <StatusBadge status={item.health_status} size="sm" />
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {item.risk_factors.length > 0 ? item.risk_factors[0].title : 'Inactive engagement'}
                      </p>
                    </div>

                    <div className="text-right font-mono">
                      <div className="font-extrabold text-rose-400 text-sm">
                        Health Score: {item.health_score}/100
                      </div>
                      <p className="text-[10px] text-slate-500 font-bold uppercase">{item.risk_level} risk</p>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Recent Pipeline Opportunities */}
          <GlassCard
            title="Recent Pipeline Opportunities"
            subtitle="Top deals currently progressing through sales stages"
            action={
              <BrutalButton variant="ghost" size="sm" icon={ArrowRight} onClick={() => navigate('/deals')}>
                View Pipeline
              </BrutalButton>
            }
          >
            {deals.length === 0 ? (
              <div className="p-6 text-center bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                <p className="text-xs font-bold text-slate-200 font-mono uppercase tracking-wider">NO ACTIVE SALES PIPELINE</p>
                <p className="text-xs text-slate-400">Create your first deal opportunity to start seeing pipeline intelligence.</p>
                <div className="pt-2">
                  <BrutalButton variant="primary" size="sm" icon={Plus} onClick={() => navigate('/deals')}>
                    Create First Deal
                  </BrutalButton>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {deals.slice(0, 5).map((deal) => (
                  <div
                    key={deal.id}
                    onClick={() => navigate(`/deals/${deal.id}`)}
                    className="py-3 flex items-center justify-between gap-4 hover:bg-slate-800/40 px-3 rounded-xl transition cursor-pointer group"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100 text-sm group-hover:text-indigo-300 transition">
                          {deal.title}
                        </span>
                        <StatusBadge status={deal.stage} size="sm" />
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-sans">{deal.customer?.name || 'Account'}</p>
                    </div>

                    <div className="text-right font-mono">
                      <span className="font-black text-slate-100 text-sm">
                        ${Number(deal.value || 0).toLocaleString()}
                      </span>
                      <p className="text-[10px] text-slate-500 font-bold">{deal.probability}% win prob</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        {/* Right Column (1 span) - Customers Going Cold & Quick AI Assistant */}
        <div className="space-y-8">
          {/* Customers Going Cold Card */}
          {intel && intel.customers_going_cold.length > 0 && (
            <GlassCard
              title={
                <span className="flex items-center gap-2 text-amber-300">
                  <Flame className="w-5 h-5 text-amber-400" />
                  Customers Going Cold
                </span>
              }
              subtitle="Accounts with declining interaction velocity"
            >
              <div className="space-y-3">
                {intel.customers_going_cold.map((cust) => (
                  <div
                    key={cust.customer_id}
                    onClick={() => navigate(`/customers/${cust.customer_id}`)}
                    className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs hover:border-amber-500/30 transition cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-100">{cust.customer_name}</span>
                      <StatusBadge status={cust.engagement_status} size="sm" />
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {cust.risk_reasons.length > 0 ? cust.risk_reasons[0] : 'Low activity count'}
                    </p>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Quick AI Assistant Card */}
          <AIInsightCard title="Ask DealFlow360 AI">
            <form onSubmit={handleAskAi} className="space-y-3">
              <input
                type="text"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                placeholder="Ask about pipeline, deals, or follow-ups..."
                className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-lg text-xs font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <BrutalButton
                type="submit"
                variant="ai"
                size="sm"
                fullWidth
                isLoading={isAiLoading}
              >
                ✦ Analyze Telemetry
              </BrutalButton>
            </form>

            {aiAnswer && (
              <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-300 leading-relaxed font-mono">
                <p className="p-3 bg-slate-950/90 rounded-xl border border-indigo-500/40 shadow-neo-sm">
                  {aiAnswer.answer}
                </p>
              </div>
            )}
          </AIInsightCard>
        </div>
      </div>
    </div>
  );
};

