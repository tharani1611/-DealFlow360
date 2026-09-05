import React from 'react';
import { Deal, DealStage } from '../../types';
import { ArrowRight, DollarSign } from 'lucide-react';

export interface KanbanBoardProps {
  deals: Deal[];
  onDealClick: (deal: Deal) => void;
  onMoveStage?: (dealId: string, currentStage: DealStage) => void;
}

const PIPELINE_STAGES: { stage: DealStage; label: string; color: string }[] = [
  { stage: 'new', label: 'New', color: 'border-t-sky-500' },
  { stage: 'qualified', label: 'Qualified', color: 'border-t-amber-500' },
  { stage: 'proposal', label: 'Proposal', color: 'border-t-indigo-500' },
  { stage: 'negotiation', label: 'Negotiation', color: 'border-t-purple-500' },
  { stage: 'won', label: 'Won', color: 'border-t-emerald-500' },
  { stage: 'lost', label: 'Lost', color: 'border-t-rose-500' },
];

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  deals,
  onDealClick,
  onMoveStage,
}) => {
  const getDealsForStage = (stage: DealStage) => deals.filter((d) => d.stage === stage);

  const getStageTotal = (stage: DealStage) => {
    return getDealsForStage(stage).reduce((acc, d) => acc + Number(d.value || 0), 0);
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-6 pt-2 select-none min-h-[500px]">
      {PIPELINE_STAGES.map(({ stage, label, color }) => {
        const stageDeals = getDealsForStage(stage);
        const total = getStageTotal(stage);

        return (
          <div
            key={stage}
            className={`flex-1 min-w-[280px] max-w-[320px] bg-slate-900/60 backdrop-blur-glass border border-slate-800 border-t-4 ${color} rounded-xl p-3 flex flex-col gap-3 shadow-neo-sm`}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-slate-100 uppercase tracking-wider text-xs">{label}</span>
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-mono font-bold">
                  {stageDeals.length}
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-slate-400">
                ${total.toLocaleString()}
              </span>
            </div>

            {/* Column Cards */}
            <div className="flex flex-col gap-3 flex-1 overflow-y-auto">
              {stageDeals.length === 0 ? (
                <div className="border border-dashed border-slate-800 rounded-lg p-6 text-center text-slate-600 text-xs font-mono">
                  No deals
                </div>
              ) : (
                stageDeals.map((deal) => (
                  <div
                    key={deal.id}
                    onClick={() => onDealClick(deal)}
                    className="bg-slate-900 border border-slate-700/80 hover:border-indigo-500/60 rounded-xl p-4 shadow-neo-sm hover:shadow-neo transition-all cursor-pointer group"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="font-bold text-slate-100 text-xs line-clamp-2 group-hover:text-indigo-300 transition">
                        {deal.title}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">{deal.deal_number}</span>
                    </div>

                    {deal.customer?.name && (
                      <p className="text-[11px] text-slate-400 font-medium mb-3">{deal.customer.name}</p>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                      <div className="flex items-center gap-1 text-slate-100 font-mono font-black text-sm">
                        <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                        <span>{Number(deal.value || 0).toLocaleString()}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-slate-400 font-bold">{deal.probability}% win</span>
                        {onMoveStage && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onMoveStage(deal.id, deal.stage);
                            }}
                            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-indigo-400 transition"
                            title="Move Stage"
                          >
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
