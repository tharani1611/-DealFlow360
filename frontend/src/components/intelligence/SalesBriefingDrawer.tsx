import React, { useState } from 'react';
import { Sparkles, Copy, Check, MessageSquare, Calendar, AlertCircle, User, Mail, ArrowUpRight, Plus, TrendingUp } from 'lucide-react';
import { SalesBriefingResponse, ProductRecommendationItem, RevenueForecastResponse } from '../../types';
import { GlassDrawer } from '../ui/GlassDrawer';
import { BrutalButton } from '../ui/BrutalButton';
import { StatusBadge } from '../ui/StatusBadge';

interface SalesBriefingDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  briefing: SalesBriefingResponse | null;
  isLoading?: boolean;
  recommendations?: ProductRecommendationItem[];
  forecast?: RevenueForecastResponse | null;
  onCreateActivity?: (action: { title: string; action_type: string; priority: string }) => void;
}

export const SalesBriefingDrawer: React.FC<SalesBriefingDrawerProps> = ({
  isOpen,
  onClose,
  briefing,
  isLoading,
  recommendations,
  forecast,
  onCreateActivity
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (briefing?.suggested_followup_message) {
      navigator.clipboard.writeText(briefing.suggested_followup_message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <GlassDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2 text-indigo-300">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <span>Executive Sales & Account Briefing</span>
        </div>
      }
    >
      {isLoading || !briefing ? (
        <div className="space-y-4 p-4 animate-pulse">
          <div className="h-8 bg-white/10 rounded w-1/2"></div>
          <div className="h-24 bg-white/5 rounded"></div>
          <div className="h-32 bg-white/5 rounded"></div>
        </div>
      ) : (
        <div className="space-y-6 text-slate-200">
          {/* Header Account Snapshot */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-900/30 to-purple-900/30 border border-indigo-500/30 backdrop-blur-md">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">{briefing.customer_name}</h2>
                {briefing.primary_contact_name && (
                  <p className="text-xs text-indigo-200 flex items-center gap-1.5 mt-0.5">
                    <User className="w-3.5 h-3.5 text-indigo-400" />
                    Primary Contact: <span className="font-semibold text-white">{briefing.primary_contact_name}</span>
                    {briefing.primary_contact_email && ` (${briefing.primary_contact_email})`}
                  </p>
                )}
              </div>
              <StatusBadge
                status={briefing.relationship_status}
                variant={
                  briefing.engagement_score >= 80 ? 'success' :
                  briefing.engagement_score >= 60 ? 'info' :
                  briefing.engagement_score >= 40 ? 'warning' : 'danger'
                }
              />
            </div>

            <div className="grid grid-cols-3 gap-3 pt-3 border-t border-white/10 text-center font-mono">
              <div className="p-2 rounded bg-black/20 border border-white/5">
                <div className="text-[10px] uppercase text-slate-400 font-sans">Engagement</div>
                <div className="text-lg font-bold text-indigo-300">{briefing.engagement_score}/100</div>
              </div>
              <div className="p-2 rounded bg-black/20 border border-white/5">
                <div className="text-[10px] uppercase text-slate-400 font-sans">Pipeline Value</div>
                <div className="text-lg font-bold text-emerald-400">${briefing.open_pipeline_value}</div>
              </div>
              <div className="p-2 rounded bg-black/20 border border-white/5">
                <div className="text-[10px] uppercase text-slate-400 font-sans">Active Deals</div>
                <div className="text-lg font-bold text-cyan-300">{briefing.active_deals_count}</div>
              </div>
            </div>
          </div>

          {/* Attention Items & Risks */}
          {briefing.attention_items.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 backdrop-blur-sm">
              <h3 className="text-xs font-bold uppercase tracking-wider text-amber-300 flex items-center gap-1.5 mb-2">
                <AlertCircle className="w-4 h-4" />
                Attention Needed Before Interaction
              </h3>
              <ul className="space-y-1 text-xs text-slate-200">
                {briefing.attention_items.map((item, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Revenue Forecast Position Section */}
          {forecast && (
            <div className="p-4 rounded-xl bg-black/30 border border-indigo-500/30 backdrop-blur-md font-mono text-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5 mb-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Revenue Forecast Position
              </h3>
              <div className="grid grid-cols-3 gap-2 text-center pt-1">
                <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Forecast</div>
                  <div className="font-bold text-emerald-400 text-xs">${Number(forecast.forecast_revenue).toLocaleString()}</div>
                </div>
                <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Committed</div>
                  <div className="font-bold text-cyan-300 text-xs">${Number(forecast.committed_revenue).toLocaleString()}</div>
                </div>
                <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">At Risk</div>
                  <div className="font-bold text-rose-400 text-xs">${Number(forecast.at_risk_revenue).toLocaleString()}</div>
                </div>
              </div>
            </div>
          )}

          {/* Recommended Talking Points */}
          <div className="p-4 rounded-xl bg-black/30 border border-white/10 backdrop-blur-md">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5 mb-3">
              <MessageSquare className="w-4 h-4" />
              Recommended Conversation Talking Points
            </h3>
            <ul className="space-y-2">
              {briefing.talking_points.map((tp, idx) => (
                <li key={idx} className="p-2.5 rounded-lg bg-white/5 border border-white/5 text-xs text-slate-200 flex items-start gap-2">
                  <span className="font-mono text-indigo-400 font-bold">{idx + 1}.</span>
                  <span>{tp}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Product Expansion & Opportunities */}
          {recommendations && recommendations.length > 0 && (
            <div className="p-4 rounded-xl bg-black/30 border border-emerald-500/30 backdrop-blur-md">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5 mb-3">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Potential Upsell & Cross-Sell Opportunities ({recommendations.length})
              </h3>
              <div className="space-y-2">
                {recommendations.map((rec) => (
                  <div key={rec.product_id} className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs font-mono">
                    <div className="flex items-center justify-between font-bold text-white mb-1">
                      <span className="text-slate-100">{rec.product_name}</span>
                      <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-mono font-bold flex items-center gap-1 ${
                        rec.recommendation_type === 'upsell'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                      }`}>
                        {rec.recommendation_type === 'upsell' ? <ArrowUpRight className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                        {rec.recommendation_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed font-sans">{rec.reason}</p>
                    <div className="text-[10px] text-slate-400 mt-1">
                      Target Unit Price: <span className="font-bold text-slate-200">${Number(rec.unit_price).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggested Next Best Action */}
          {briefing.suggested_next_actions.length > 0 && (
            <div className="p-4 rounded-xl bg-black/30 border border-white/10 backdrop-blur-md">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5 mb-3">
                <Calendar className="w-4 h-4" />
                Recommended Next Action
              </h3>
              {briefing.suggested_next_actions.map((act, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs">
                  <div>
                    <div className="font-semibold text-white text-sm">{act.title}</div>
                    <div className="text-[11px] text-slate-300 capitalize mt-0.5">
                      Type: {act.action_type} | Priority: {act.priority}
                    </div>
                  </div>
                  {onCreateActivity && (
                    <BrutalButton
                      variant="primary"
                      size="sm"
                      onClick={() => onCreateActivity(act)}
                    >
                      Create Activity
                    </BrutalButton>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Pre-drafted Follow-up Message */}
          {briefing.suggested_followup_message && (
            <div className="p-4 rounded-xl bg-black/30 border border-white/10 backdrop-blur-md">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center gap-1.5">
                  <Mail className="w-4 h-4" />
                  Pre-Drafted Follow-Up Message
                </h3>
                <BrutalButton
                  variant="secondary"
                  size="sm"
                  onClick={handleCopy}
                  className="text-xs py-1"
                >
                  {copied ? (
                    <span className="flex items-center gap-1 text-emerald-400">
                      <Check className="w-3.5 h-3.5" /> Copied
                    </span>
                  ) : (
                    <span className="flex items-center gap-1">
                      <Copy className="w-3.5 h-3.5" /> Copy Message
                    </span>
                  )}
                </BrutalButton>
              </div>
              <textarea
                readOnly
                rows={4}
                className="w-full p-3 rounded-lg bg-black/40 border border-white/10 font-mono text-xs text-slate-200 resize-none focus:outline-none"
                value={briefing.suggested_followup_message}
              />
            </div>
          )}
        </div>
      )}
    </GlassDrawer>
  );
};
