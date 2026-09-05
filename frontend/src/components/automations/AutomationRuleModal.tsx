import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassInput } from '../ui/GlassInput';
import { GlassSelect } from '../ui/GlassSelect';
import { GlassTextarea } from '../ui/GlassTextarea';
import { BrutalButton } from '../ui/BrutalButton';
import { AutomationRule, AutomationRuleCreate, AutomationCondition, AutomationAction } from '../../types';
import { Plus, Trash2, Layers, CheckCircle2 } from 'lucide-react';

interface AutomationRuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: AutomationRuleCreate) => Promise<void>;
  initialRule?: AutomationRule | null;
  isLoading?: boolean;
}

const TRIGGER_OPTIONS = [
  { value: 'DEAL_STAGE_CHANGED', label: 'Deal Stage Changed' },
  { value: 'DEAL_CREATED', label: 'Deal Created' },
  { value: 'QUOTATION_EXPIRED', label: 'Quotation Expired' },
  { value: 'QUOTATION_STATE_CHANGED', label: 'Quotation Status Changed' },
  { value: 'ACTIVITY_OVERDUE', label: 'Activity Overdue' },
  { value: 'CUSTOMER_COOLING_DETECTED', label: 'Customer Relationship Cooling' },
  { value: 'APPROVAL_REQUESTED', label: 'Commercial Approval Requested' },
];

const OPERATOR_OPTIONS = [
  { value: 'equals', label: 'Equals (=)' },
  { value: 'not_equals', label: 'Not Equals (≠)' },
  { value: 'greater_than', label: 'Greater Than (>)' },
  { value: 'less_than', label: 'Less Than (<)' },
  { value: 'contains', label: 'Contains' },
  { value: 'is_empty', label: 'Is Empty' },
  { value: 'is_not_empty', label: 'Is Not Empty' },
];

const ACTION_TYPE_OPTIONS = [
  { value: 'CREATE_ACTIVITY', label: 'Create Follow-up Activity' },
  { value: 'CREATE_TASK', label: 'Create Task Item' },
  { value: 'SEND_NOTIFICATION', label: 'Send Notification Alert' },
  { value: 'ASSIGN_DEAL', label: 'Reassign / Add Deal Note' },
  { value: 'UPDATE_DEAL_FIELD', label: 'Update Deal Field' },
];

export const AutomationRuleModal: React.FC<AutomationRuleModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialRule,
  isLoading = false
}) => {
  const [name, setName] = useState(initialRule?.name || '');
  const [description, setDescription] = useState(initialRule?.description || '');
  const [triggerType, setTriggerType] = useState(initialRule?.trigger_type || 'DEAL_STAGE_CHANGED');
  const [priority, setPriority] = useState(initialRule?.priority || 10);
  const [logicalOp, setLogicalOp] = useState<'AND' | 'OR'>(initialRule?.conditions?.logical_operator || 'AND');

  const [conditions, setConditions] = useState<AutomationCondition[]>(
    initialRule?.conditions?.conditions && initialRule.conditions.conditions.length > 0
      ? initialRule.conditions.conditions
      : [{ field: 'deal.stage', operator: 'equals', value: 'proposal' }]
  );

  const [actions, setActions] = useState<AutomationAction[]>(
    initialRule?.actions && initialRule.actions.length > 0
      ? initialRule.actions
      : [
          {
            action_type: 'CREATE_ACTIVITY',
            parameters: { title: 'Automated Follow-up', activity_type: 'call', priority: 'high', due_in_days: 2 }
          }
        ]
  );

  const [error, setError] = useState<string | null>(null);

  const handleAddCondition = () => {
    setConditions([...conditions, { field: 'deal.value', operator: 'greater_than', value: '50000' }]);
  };

  const handleRemoveCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleConditionChange = (index: number, field: keyof AutomationCondition, val: any) => {
    const next = [...conditions];
    next[index] = { ...next[index], [field]: val };
    setConditions(next);
  };

  const handleAddAction = () => {
    setActions([
      ...actions,
      {
        action_type: 'SEND_NOTIFICATION',
        parameters: { title: 'Workflow Alert', message: 'High priority event occurred', severity: 'info' }
      }
    ]);
  };

  const handleRemoveAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
  };

  const handleActionChange = (index: number, action_type: string) => {
    const next = [...actions];
    next[index] = {
      action_type,
      parameters: action_type === 'CREATE_ACTIVITY'
        ? { title: 'Automated Follow-up', activity_type: 'call', priority: 'high', due_in_days: 2 }
        : action_type === 'SEND_NOTIFICATION'
        ? { title: 'Workflow Alert', message: 'Event notification', severity: 'warning' }
        : { note: 'Workflow execution note' }
    };
    setActions(next);
  };

  const handleActionParamChange = (index: number, paramKey: string, val: any) => {
    const next = [...actions];
    next[index] = {
      ...next[index],
      parameters: { ...next[index].parameters, [paramKey]: val }
    };
    setActions(next);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Rule name is required.');
      return;
    }
    if (actions.length === 0) {
      setError('At least one action must be configured.');
      return;
    }

    setError(null);
    try {
      await onSave({
        name: name.trim(),
        description: description.trim() || undefined,
        trigger_type: triggerType,
        priority: Number(priority),
        conditions: {
          logical_operator: logicalOp,
          conditions: conditions
        },
        actions: actions
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save automation rule.');
    }
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={initialRule ? 'Edit Automation Rule' : 'Create Automation Rule'}
      maxWidth="2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-6 font-mono text-xs">
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-bold">
            ⚠ {error}
          </div>
        )}

        {/* Basic Metadata */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <GlassInput
            label="Rule Name *"
            placeholder="e.g. Follow-up on High Value Proposal"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <GlassSelect
            label="Trigger Event *"
            value={triggerType}
            onChange={(e) => setTriggerType(e.target.value)}
            options={TRIGGER_OPTIONS}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="sm:col-span-3">
            <GlassTextarea
              label="Description"
              placeholder="Explain what this automation rule does..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>
          <GlassInput
            label="Priority (Higher = First)"
            type="number"
            value={priority.toString()}
            onChange={(e) => setPriority(parseInt(e.target.value) || 0)}
          />
        </div>

        {/* Visual Condition Builder */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-indigo-300 uppercase tracking-wider text-[11px]">
              Conditions (IF Match Criteria)
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-slate-400 font-sans">Logic:</span>
              <button
                type="button"
                onClick={() => setLogicalOp(logicalOp === 'AND' ? 'OR' : 'AND')}
                className="px-2.5 py-1 rounded bg-indigo-600/40 border border-indigo-500/40 text-indigo-200 font-bold text-[10px] uppercase"
              >
                Match {logicalOp}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {conditions.map((cond, idx) => (
              <div key={idx} className="flex items-center gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                <input
                  type="text"
                  placeholder="e.g. deal.value"
                  value={cond.field}
                  onChange={(e) => handleConditionChange(idx, 'field', e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                />
                <select
                  value={cond.operator}
                  onChange={(e) => handleConditionChange(idx, 'operator', e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300 text-xs focus:border-indigo-500 outline-none"
                >
                  {OPERATOR_OPTIONS.map((op) => (
                    <option key={op.value} value={op.value}>{op.label}</option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Target Value"
                  value={cond.value || ''}
                  onChange={(e) => handleConditionChange(idx, 'value', e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveCondition(idx)}
                  className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/20 rounded"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={handleAddCondition}
            className="flex items-center gap-1.5 text-[11px] font-bold text-indigo-400 hover:text-indigo-300 pt-1"
          >
            <Plus className="w-3.5 h-3.5" /> Add Condition
          </button>
        </div>

        {/* Visual Action Builder */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <span className="font-bold text-emerald-300 uppercase tracking-wider text-[11px] block">
            Actions (THEN Execution Pipeline)
          </span>

          <div className="space-y-3">
            {actions.map((act, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <select
                    value={act.action_type}
                    onChange={(e) => handleActionChange(idx, e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 text-xs font-bold focus:border-emerald-500 outline-none"
                  >
                    {ACTION_TYPE_OPTIONS.map((a) => (
                      <option key={a.value} value={a.value}>{a.label}</option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={() => handleRemoveAction(idx)}
                    className="p-1 text-slate-400 hover:text-rose-400 hover:bg-rose-500/20 rounded"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Param fields based on action_type */}
                {act.action_type === 'CREATE_ACTIVITY' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <input
                      type="text"
                      placeholder="Title e.g. Follow-up Call"
                      value={act.parameters.title || ''}
                      onChange={(e) => handleActionParamChange(idx, 'title', e.target.value)}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 outline-none focus:border-emerald-500"
                    />
                    <select
                      value={act.parameters.priority || 'medium'}
                      onChange={(e) => handleActionParamChange(idx, 'priority', e.target.value)}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 outline-none focus:border-emerald-500"
                    >
                      <option value="low">Low Priority</option>
                      <option value="medium">Medium Priority</option>
                      <option value="high">High Priority</option>
                      <option value="urgent">Urgent Priority</option>
                    </select>
                  </div>
                )}

                {act.action_type === 'SEND_NOTIFICATION' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <input
                      type="text"
                      placeholder="Notification Title"
                      value={act.parameters.title || ''}
                      onChange={(e) => handleActionParamChange(idx, 'title', e.target.value)}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 outline-none focus:border-emerald-500"
                    />
                    <select
                      value={act.parameters.severity || 'warning'}
                      onChange={(e) => handleActionParamChange(idx, 'severity', e.target.value)}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 outline-none focus:border-emerald-500"
                    >
                      <option value="info">Info Alert</option>
                      <option value="warning">Warning Alert</option>
                      <option value="critical">Critical Alert</option>
                    </select>
                  </div>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={handleAddAction}
            className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-400 hover:text-emerald-300 pt-1"
          >
            <Plus className="w-3.5 h-3.5" /> Add Action
          </button>
        </div>

        {/* Human Readable Rule Preview */}
        <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/30 font-mono text-[11px] space-y-1 text-slate-300">
          <span className="font-bold text-indigo-300 uppercase tracking-wider block text-[10px] flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            Human-Readable Workflow Logic Preview
          </span>
          <div>
            <span className="text-indigo-400 font-bold">WHEN: </span>
            <span>{TRIGGER_OPTIONS.find((t) => t.value === triggerType)?.label}</span>
          </div>
          <div>
            <span className="text-indigo-400 font-bold">IF ({logicalOp}): </span>
            <span>
              {conditions.length > 0
                ? conditions.map((c) => `${c.field} ${c.operator} "${c.value || ''}"`).join(` ${logicalOp} `)
                : 'Always execute'}
            </span>
          </div>
          <div>
            <span className="text-emerald-400 font-bold">THEN: </span>
            <span>{actions.map((a) => a.action_type).join(' AND ')}</span>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2 border-t border-slate-800">
          <BrutalButton variant="ghost" onClick={onClose} type="button">
            Cancel
          </BrutalButton>
          <BrutalButton variant="primary" type="submit" isLoading={isLoading} icon={CheckCircle2}>
            Save Rule
          </BrutalButton>
        </div>
      </form>
    </GlassModal>
  );
};
