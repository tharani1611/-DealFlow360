import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dealApi } from '../services/dealApi';
import { customerApi } from '../services/customerApi';
import { Deal, Customer, DealStage } from '../types';
import { KanbanBoard } from '../components/ui/KanbanBoard';
import { DataTable, Column } from '../components/ui/DataTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassModal } from '../components/ui/GlassModal';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { Plus, LayoutGrid, List } from 'lucide-react';

export const DealsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [deals, setDeals] = useState<Deal[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [viewMode, setViewMode] = useState<'kanban' | 'list'>('kanban');

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [title, setTitle] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [value, setValue] = useState('');
  const [probability, setProbability] = useState('20');
  const [stage, setStage] = useState<DealStage>('new');

  // Stage Transition Modal State
  const [transitionDealId, setTransitionDealId] = useState<string | null>(null);
  const [newStageTarget, setNewStageTarget] = useState<DealStage>('qualified');
  const [lostReason, setLostReason] = useState('');
  const [isTransitioning, setIsTransitioning] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dealsData, custData] = await Promise.all([dealApi.getDeals(), customerApi.getCustomers()]);
      setDeals(dealsData);
      setCustomers(custData);
      if (custData.length > 0 && !customerId) setCustomerId(custData[0].id);
    } catch (err: any) {
      setError(err.message || 'Failed to load deal pipeline.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateDeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !customerId) return;

    setIsSaving(true);
    try {
      const created = await dealApi.createDeal({
        title: title.trim(),
        customer_id: customerId,
        value: value ? parseFloat(value) : 0,
        probability: parseInt(probability, 10) || 10,
        stage,
      });
      showToast(`Deal "${created.title}" added to pipeline!`, 'success');
      setIsModalOpen(false);
      setTitle('');
      setValue('');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to create deal.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleStageTransitionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transitionDealId) return;

    if (newStageTarget === 'lost' && !lostReason.trim()) {
      showToast('Lost reason is required when transitioning to Lost stage.', 'warning');
      return;
    }

    setIsTransitioning(true);
    try {
      await dealApi.transitionDealStage(transitionDealId, newStageTarget, lostReason.trim() || undefined);
      showToast('Deal stage updated successfully.', 'success');
      setTransitionDealId(null);
      setLostReason('');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to transition stage.', 'error');
    } finally {
      setIsTransitioning(false);
    }
  };

  const columns: Column<Deal>[] = [
    {
      header: 'Deal Title',
      render: (r) => (
        <div>
          <span className="font-extrabold text-slate-100 text-sm">{r.title}</span>
          <span className="text-[10px] font-mono text-slate-500 block">{r.deal_number}</span>
        </div>
      ),
    },
    {
      header: 'Customer',
      render: (r) => <span className="text-xs font-semibold text-slate-200">{r.customer?.name || '—'}</span>,
    },
    {
      header: 'Value',
      render: (r) => (
        <span className="font-mono font-black text-slate-100 text-sm">
          ₹{Number(r.value || 0).toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Probability',
      render: (r) => <span className="font-mono text-xs text-slate-400">{r.probability}%</span>,
    },
    {
      header: 'Stage',
      render: (r) => <StatusBadge status={r.stage} size="sm" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Sales Pipeline Command</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Visualize pipeline progression, win probabilities, and deal velocity
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('kanban')}
              className={`p-1.5 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                viewMode === 'kanban' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Kanban</span>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                viewMode === 'list' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>List</span>
            </button>
          </div>

          <BrutalButton variant="primary" icon={Plus} onClick={() => setIsModalOpen(true)}>
            New Deal
          </BrutalButton>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Loading sales pipeline data..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : viewMode === 'kanban' ? (
        <KanbanBoard
          deals={deals}
          onDealClick={(deal) => navigate(`/deals/${deal.id}`)}
          onMoveStage={(dealId, currentStage) => {
            setTransitionDealId(dealId);
            setNewStageTarget(currentStage === 'new' ? 'qualified' : 'proposal');
          }}
        />
      ) : (
        <DataTable
          columns={columns}
          data={deals}
          keyExtractor={(r) => r.id}
          emptyMessage="No deals active in pipeline."
          onRowClick={(r) => navigate(`/deals/${r.id}`)}
        />
      )}

      {/* Create Deal Modal */}
      <GlassModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Pipeline Opportunity"
        subtitle="Add a new sales deal to the pipeline"
      >
        <form onSubmit={handleCreateDeal} className="space-y-4">
          <GlassInput
            label="Deal Title"
            placeholder="e.g. Enterprise Cloud Deployment"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />

          <GlassSelect
            label="Customer Account"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            options={customers.map((c) => ({ value: c.id, label: c.name }))}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <GlassInput
              label="Deal Value (₹)"
              type="number"
              placeholder="50000"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
            <GlassSelect
              label="Initial Stage"
              value={stage}
              onChange={(e) => setStage(e.target.value as DealStage)}
              options={[
                { value: 'new', label: 'New' },
                { value: 'qualified', label: 'Qualified' },
                { value: 'proposal', label: 'Proposal' },
                { value: 'negotiation', label: 'Negotiation' },
              ]}
            />
          </div>

          <GlassInput
            label="Win Probability (%)"
            type="number"
            min="0"
            max="100"
            value={probability}
            onChange={(e) => setProbability(e.target.value)}
          />

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSaving}>
              Save Deal
            </BrutalButton>
          </div>
        </form>
      </GlassModal>

      {/* Stage Transition Modal */}
      <GlassModal
        isOpen={!!transitionDealId}
        onClose={() => setTransitionDealId(null)}
        title="Transition Deal Stage"
        subtitle="Advance or update sales stage for this deal"
      >
        <form onSubmit={handleStageTransitionSubmit} className="space-y-4">
          <GlassSelect
            label="Target Stage"
            value={newStageTarget}
            onChange={(e) => setNewStageTarget(e.target.value as DealStage)}
            options={[
              { value: 'new', label: 'New' },
              { value: 'qualified', label: 'Qualified' },
              { value: 'proposal', label: 'Proposal' },
              { value: 'negotiation', label: 'Negotiation' },
              { value: 'won', label: 'Won (Closed)' },
              { value: 'lost', label: 'Lost (Closed)' },
            ]}
          />

          {newStageTarget === 'lost' && (
            <GlassInput
              label="Lost Reason (Required)"
              placeholder="e.g. Competitor pricing or feature gap"
              value={lostReason}
              onChange={(e) => setLostReason(e.target.value)}
              required
            />
          )}

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setTransitionDealId(null)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isTransitioning}>
              Update Stage
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
