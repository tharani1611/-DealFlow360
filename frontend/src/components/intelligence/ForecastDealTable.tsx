import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, AlertCircle } from 'lucide-react';
import { DealForecastItem, ForecastCategory } from '../../types';
import { DataTable, Column } from '../ui/DataTable';

interface ForecastDealTableProps {
  deals: DealForecastItem[];
}

export const ForecastDealTable: React.FC<ForecastDealTableProps> = ({ deals }) => {
  const navigate = useNavigate();

  const getCategoryBadge = (cat: ForecastCategory) => {
    switch (cat) {
      case 'COMMITTED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            COMMITTED
          </span>
        );
      case 'UPSIDE':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
            UPSIDE
          </span>
        );
      case 'AT_RISK':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 text-rose-400" /> AT RISK
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700">
            PIPELINE
          </span>
        );
    }
  };

  const columns: Column<DealForecastItem>[] = [
    {
      header: 'Deal & Customer',
      render: (r) => (
        <div className="cursor-pointer" onClick={() => navigate(`/deals/${r.deal_id}`)}>
          <div className="flex items-center gap-1.5 font-bold text-slate-100 hover:text-indigo-300 transition">
            <span>{r.title}</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <span className="text-[10px] text-slate-400 font-mono block">
            {r.customer_name} ({r.deal_number})
          </span>
        </div>
      ),
    },
    {
      header: 'Forecast Category',
      render: (r) => getCategoryBadge(r.forecast_category),
    },
    {
      header: 'Deal Value',
      render: (r) => (
        <div className="font-mono">
          <span className="font-extrabold text-slate-100 block">₹{Number(r.value).toLocaleString()}</span>
          <span className="text-[10px] text-emerald-400">Fcst: ₹{Number(r.forecast_value).toLocaleString()}</span>
        </div>
      ),
    },
    {
      header: 'Stage & Health',
      render: (r) => (
        <div className="font-mono text-xs">
          <span className="capitalize text-slate-300 font-bold block">{r.stage}</span>
          <span className="text-[10px] text-slate-400">Score: {r.health_score}/100</span>
        </div>
      ),
    },
    {
      header: 'Probability Model',
      render: (r) => (
        <div className="font-mono text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Base: {r.base_probability}%</span>
            <span>➔</span>
            <span className="font-bold text-indigo-300">Adj: {r.adjusted_probability}%</span>
          </div>
        </div>
      ),
    },
    {
      header: 'Close Date',
      render: (r) => (
        <span className="font-mono text-xs text-slate-300">
          {r.expected_close_date || 'Unscheduled'}
        </span>
      ),
    },
    {
      header: 'Forecast Driver',
      render: (r) => (
        <div className="text-[11px] font-mono max-w-xs">
          {r.forecast_category === 'AT_RISK' ? (
            <span className="text-rose-300">{r.primary_negative_factor}</span>
          ) : (
            <span className="text-emerald-300">{r.primary_positive_factor}</span>
          )}
        </div>
      ),
    },
  ];

  return (
    <DataTable
      data={deals}
      columns={columns}
      keyExtractor={(r) => r.deal_id}
      emptyMessage="No deals match the selected forecast query parameters."
    />
  );
};
