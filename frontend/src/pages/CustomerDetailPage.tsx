import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { customerApi } from '../services/customerApi';
import { contactApi } from '../services/contactApi';
import { quotationApi } from '../services/quotationApi';
import { dealApi } from '../services/dealApi';
import { activityApi } from '../services/activityApi';
import { aiApi } from '../services/aiApi';
import { intelligenceApi } from '../services/intelligenceApi';
import { forecastApi } from '../services/forecastApi';
import {
  Customer,
  Contact,
  Quotation,
  Deal,
  Activity,
  CustomerSummaryResponse,
  CustomerEngagementResponse,
  Customer360Intelligence,
  SalesBriefingResponse,
  ProductRecommendationItem,
  RevenueForecastResponse
} from '../types';
import { Tabs } from '../components/ui/Tabs';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { SalesBriefingDrawer } from '../components/intelligence/SalesBriefingDrawer';
import { ProductOpportunityCard } from '../components/intelligence/ProductOpportunityCard';
import { CustomerHealthCard } from '../components/intelligence/CustomerHealthCard';
import { Timeline } from '../components/ui/Timeline';
import { DataTable, Column } from '../components/ui/DataTable';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { ArrowLeft, Mail, Phone, MapPin, Sparkles, Activity as ActivityIcon, TrendingUp } from 'lucide-react';

export const CustomerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [aiSummary, setAiSummary] = useState<CustomerSummaryResponse | null>(null);
  const [engagement, setEngagement] = useState<CustomerEngagementResponse | null>(null);
  const [cust360, setCust360] = useState<Customer360Intelligence | null>(null);
  const [briefing, setBriefing] = useState<SalesBriefingResponse | null>(null);
  const [recommendations, setRecommendations] = useState<ProductRecommendationItem[]>([]);
  const [custForecast, setCustForecast] = useState<RevenueForecastResponse | null>(null);

  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [isBriefingLoading, setIsBriefingLoading] = useState(false);
  const [isBriefingOpen, setIsBriefingOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCustomerDetails = async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [custData, contactsData, quotesData, dealsData, actData, engData, c360Data, recData, fcData] = await Promise.all([
        customerApi.getCustomer(id),
        contactApi.getContacts({ customer_id: id }),
        quotationApi.getQuotations({ customer_id: id }),
        dealApi.getDeals({ customer_id: id }),
        activityApi.getCustomerActivities(id),
        intelligenceApi.getCustomerEngagement(id).catch(() => null),
        intelligenceApi.getCustomer360(id).catch(() => null),
        intelligenceApi.getCustomerProductRecommendations(id).catch(() => null),
        forecastApi.getForecast({ customer_id: id }).catch(() => null),
      ]);
      setCustomer(custData);
      setContacts(contactsData);
      setQuotations(quotesData);
      setDeals(dealsData);
      setActivities(actData);
      setEngagement(engData);
      setCust360(c360Data);
      setRecommendations(recData?.recommendations || []);
      setCustForecast(fcData);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve customer record details.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRecommendationActivity = async (rec: ProductRecommendationItem) => {
    if (!id) return;
    try {
      await activityApi.createActivity({
        customer_id: id,
        activity_type: 'follow_up',
        title: `Follow up on ${rec.product_name} ${rec.recommendation_type.toUpperCase()} opportunity`,
        description: rec.reason,
        priority: 'high',
      });
      showToast(`Created follow-up activity for ${rec.product_name}.`, 'success');
      const actData = await activityApi.getCustomerActivities(id);
      setActivities(actData);
    } catch (err: any) {
      showToast(err.message || 'Failed to create activity record.', 'error');
    }
  };

  useEffect(() => {
    loadCustomerDetails();
  }, [id]);

  const handleOpenBriefing = async () => {
    if (!id) return;
    setIsBriefingOpen(true);
    if (!briefing) {
      setIsBriefingLoading(true);
      try {
        const b = await intelligenceApi.getSalesBriefing(id);
        setBriefing(b);
      } catch (err: any) {
        showToast(err.message || 'Failed to load Sales Briefing.', 'error');
      } finally {
        setIsBriefingLoading(false);
      }
    }
  };

  const handleGenerateAiSummary = async () => {
    if (!id) return;
    setIsAiLoading(true);
    try {
      const res = await aiApi.getCustomerSummary(id);
      setAiSummary(res);
      showToast('AI Relationship Intelligence summary generated.', 'info');
    } catch (err: any) {
      showToast(err.message || 'Failed to generate AI summary.', 'error');
    } finally {
      setIsAiLoading(false);
    }
  };

  if (isLoading) return <LoadingState message="Loading customer record telemetry..." />;
  if (error || !customer) return <ErrorState message={error || 'Customer not found'} onRetry={loadCustomerDetails} />;

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'contacts', label: 'Contacts', count: contacts.length },
    { id: 'quotations', label: 'Quotations', count: quotations.length },
    { id: 'deals', label: 'Deals', count: deals.length },
    { id: 'activities', label: 'Activities', count: activities.length },
    { id: 'ai', label: 'AI Intelligence' },
  ];

  const contactColumns: Column<Contact>[] = [
    {
      header: 'Name',
      render: (r) => (
        <div>
          <span className="font-bold text-slate-100">{r.first_name} {r.last_name}</span>
          {r.is_primary && (
            <span className="ml-2 text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-500/40 px-1.5 py-0.5 rounded font-mono font-bold">
              PRIMARY
            </span>
          )}
        </div>
      ),
    },
    { header: 'Job Title', accessor: 'job_title' },
    { header: 'Email', accessor: 'email' },
    { header: 'Phone', accessor: 'phone' },
  ];

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/customers')}
        className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-slate-100 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Customer Directory</span>
      </button>

      {/* Customer Hero Card */}
      <GlassCard className="border-l-4 border-l-indigo-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-black text-slate-100 tracking-tight">{customer.name}</h1>
              <StatusBadge status={customer.is_active ? 'active' : 'inactive'} />
              {engagement && (
                <StatusBadge
                  status={engagement.engagement_status}
                  variant={
                    engagement.engagement_score >= 80 ? 'success' :
                    engagement.engagement_score >= 60 ? 'info' :
                    engagement.engagement_score >= 40 ? 'warning' : 'danger'
                  }
                />
              )}
            </div>

            <div className="flex items-center gap-6 mt-3 text-xs text-slate-400 font-mono flex-wrap">
              {customer.email && (
                <span className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-indigo-400" />
                  {customer.email}
                </span>
              )}
              {customer.phone && (
                <span className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-indigo-400" />
                  {customer.phone}
                </span>
              )}
              {customer.city && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                  {[customer.city, customer.state, customer.country].filter(Boolean).join(', ')}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <BrutalButton
              variant="ai"
              icon={Sparkles}
              onClick={handleOpenBriefing}
            >
              ✦ Sales Briefing
            </BrutalButton>
          </div>
        </div>
      </GlassCard>

      {/* Navigation Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Content Panels */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Customer Health & Segment Intelligence Card */}
            {cust360 && (
              <CustomerHealthCard health={cust360.health} customerName={customer.name} />
            )}

            {/* Relationship Intelligence Header & Executive Snapshot */}
            {engagement && (
              <GlassCard
                title={
                  <span className="flex items-center gap-2 text-indigo-300">
                    <ActivityIcon className="w-4 h-4 text-indigo-400" />
                    Executive Relationship Snapshot & Telemetry
                  </span>
                }
              >
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center font-mono">
                  <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-400 uppercase font-sans">Engagement Score</div>
                    <div className="text-xl font-bold text-indigo-300">{engagement.engagement_score}/100</div>
                    <div className="text-[10px] uppercase font-bold text-indigo-400 mt-0.5">{engagement.engagement_status.replace('_', ' ')}</div>
                  </div>
                  <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-400 uppercase font-sans">Open Deals Value</div>
                    <div className="text-xl font-bold text-emerald-400">₹{engagement.metrics.total_open_deal_value}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{engagement.metrics.open_deal_count} active opportunities</div>
                  </div>
                  <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-400 uppercase font-sans">Overdue Tasks</div>
                    <div className={`text-xl font-bold ${engagement.metrics.overdue_activity_count > 0 ? 'text-rose-400' : 'text-slate-200'}`}>
                      {engagement.metrics.overdue_activity_count}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{engagement.metrics.recent_activity_count_30d} recent touchpoints</div>
                  </div>
                  <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-400 uppercase font-sans font-bold">Accepted Quotes</div>
                    <div className="text-xl font-bold text-cyan-300">{engagement.metrics.accepted_quotation_count}</div>
                  </div>
                </div>

                {/* Telemetry Breakdown / "Why this score?" */}
                {(engagement.risk_reasons.length > 0 || engagement.ai_explanation) && (
                  <div className="mt-4 pt-3 border-t border-slate-800 text-xs">
                    <div className="text-[11px] font-bold font-mono text-indigo-300 uppercase tracking-wider mb-2">
                      Why this score? (Score Telemetry Breakdown)
                    </div>
                    {engagement.risk_reasons.length > 0 && (
                      <div className="space-y-1 mb-2">
                        {engagement.risk_reasons.map((reason, idx) => (
                          <div key={idx} className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px] font-mono">
                            • {reason}
                          </div>
                        ))}
                      </div>
                    )}
                    {engagement.ai_explanation && (
                      <p className="p-2.5 rounded bg-slate-950/80 border border-slate-800 text-slate-300 text-[11px] font-mono leading-relaxed">
                        "{engagement.ai_explanation}"
                      </p>
                    )}
                  </div>
                )}
              </GlassCard>
            )}

            {/* Account Details Card */}
            <GlassCard title="Account Overview" subtitle="Core organization record data">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 font-mono block">Address</span>
                  <p className="text-slate-200 font-bold mt-0.5">{customer.address || 'Unspecified'}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-mono block">Postal Code</span>
                  <p className="text-slate-200 font-bold mt-0.5">{customer.postal_code || 'Unspecified'}</p>
                </div>
              </div>
            </GlassCard>

            {/* Product Opportunities / Expansion Intelligence Card */}
            <GlassCard
              title={
                <span className="flex items-center gap-2 text-emerald-300">
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  Product Expansion & Opportunity Signals
                </span>
              }
              subtitle="Deterministic rule-based upsell & cross-sell recommendations"
            >
              {recommendations.length > 0 ? (
                <div className="space-y-3">
                  {recommendations.map((rec) => (
                    <ProductOpportunityCard
                      key={rec.product_id}
                      recommendation={rec}
                      onCreateActivity={handleCreateRecommendationActivity}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 font-mono p-2">
                  No specific expansion opportunities identified for this account based on configured rule conditions.
                </p>
              )}
            </GlassCard>
          </div>

          <div className="space-y-6">
            <GlassCard title="Quick Stats" subtitle="Account summary counters">
              <div className="space-y-3 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Total Contacts</span>
                  <span className="font-bold text-slate-100">{contacts.length}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Total Deals</span>
                  <span className="font-bold text-slate-100">{deals.length}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Total Quotations</span>
                  <span className="font-bold text-slate-100">{quotations.length}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-400">Total Activities</span>
                  <span className="font-bold text-slate-100">{activities.length}</span>
                </div>
              </div>
            </GlassCard>

            {/* Revenue Potential Card */}
            {custForecast && (
              <GlassCard
                title={
                  <span className="flex items-center gap-2 text-indigo-300">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    Account Revenue Potential
                  </span>
                }
                subtitle="Forecast revenue breakdown for this customer"
              >
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Open Pipeline:</span>
                    <span className="font-bold text-slate-100">₹{Number(custForecast.open_pipeline).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Forecast Revenue:</span>
                    <span className="font-extrabold text-emerald-400">₹{Number(custForecast.forecast_revenue).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Committed:</span>
                    <span className="font-bold text-cyan-300">₹{Number(custForecast.committed_revenue).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-400">At Risk:</span>
                    <span className="font-bold text-rose-400">₹{Number(custForecast.at_risk_revenue).toLocaleString()}</span>
                  </div>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      )}

      {activeTab === 'contacts' && (
        <GlassCard title="Associated Contacts" subtitle="Directory of people linked to this customer account">
          <DataTable data={contacts} columns={contactColumns} keyExtractor={(r) => r.id} emptyMessage="No contacts found." />
        </GlassCard>
      )}

      {activeTab === 'quotations' && (
        <GlassCard title="Commercial Quotations" subtitle="Proposals generated for this account">
          {quotations.length === 0 ? (
            <p className="text-slate-400 font-mono text-xs p-4">No quotations generated yet.</p>
          ) : (
            <div className="space-y-3">
              {quotations.map((q) => (
                <div
                  key={q.id}
                  onClick={() => navigate(`/quotations/${q.id}`)}
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-800/40 transition"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-100 font-mono">{q.quotation_number}</span>
                      <StatusBadge status={q.status} size="sm" />
                    </div>
                  </div>
                  <div className="font-mono font-bold text-emerald-400">
                    ₹{Number(q.total_amount || 0).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {activeTab === 'deals' && (
        <GlassCard title="Pipeline Deals" subtitle="Commercial sales opportunities">
          {deals.length === 0 ? (
            <p className="text-slate-400 font-mono text-xs p-4">No deals associated with this customer.</p>
          ) : (
            <div className="space-y-3">
              {deals.map((d) => (
                <div
                  key={d.id}
                  onClick={() => navigate(`/deals/${d.id}`)}
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-800/40 transition"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-100">{d.title}</span>
                      <StatusBadge status={d.stage} size="sm" />
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">{d.deal_number}</span>
                  </div>
                  <div className="font-mono font-bold text-slate-100">
                    ₹{Number(d.value || 0).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {activeTab === 'activities' && (
        <GlassCard title="Customer Activity Feed" subtitle="Audit log of interactions with this account">
          <Timeline activities={activities} />
        </GlassCard>
      )}

      {activeTab === 'ai' && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <BrutalButton
              variant="ai"
              onClick={handleGenerateAiSummary}
              isLoading={isAiLoading}
            >
              ✦ Generate AI Summary
            </BrutalButton>
          </div>

          {aiSummary ? (
            <AIInsightCard
              title={`Customer Intelligence: ${aiSummary.customer_name}`}
              provider={aiSummary.metadata.provider}
              model={aiSummary.metadata.model}
            >
              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest block mb-1">
                    Relationship Executive Summary:
                  </span>
                  <p className="text-slate-200 leading-relaxed">{aiSummary.summary}</p>
                </div>

                <div>
                  <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest block mb-1">
                    Key Insights:
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    {aiSummary.key_insights.map((insight, idx) => (
                      <li key={idx}>{insight}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </AIInsightCard>
          ) : (
            <p className="text-slate-400 font-mono text-xs text-center p-8 bg-slate-950/40 rounded-xl border border-slate-800">
              Click 'Generate AI Summary' to analyze account interaction history and pipeline context.
            </p>
          )}
        </div>
      )}

      {/* Sales Briefing Drawer */}
      <SalesBriefingDrawer
        isOpen={isBriefingOpen}
        onClose={() => setIsBriefingOpen(false)}
        briefing={briefing}
        isLoading={isBriefingLoading}
        recommendations={recommendations}
        forecast={custForecast}
        onCreateActivity={() => {
          setIsBriefingOpen(false);
          navigate(`/deals`);
        }}
      />
    </div>
  );
};
