import { fetchApi } from './apiClient';
import {
  AutomationRule,
  AutomationRuleCreate,
  AutomationRuleUpdate,
  AutomationExecution,
  AutomationAnalyticsSummary,
  AIRuleRecommendation
} from '../types';

export interface RuleQueryParams {
  status?: string;
  trigger_type?: string;
}

export interface ExecutionQueryParams {
  rule_id?: string;
  status?: string;
  event_type?: string;
}

export const automationsApi = {
  async getRules(params?: RuleQueryParams): Promise<AutomationRule[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.trigger_type) query.append('trigger_type', params.trigger_type);
    const qStr = query.toString();
    return fetchApi<AutomationRule[]>(`/automations${qStr ? `?${qStr}` : ''}`);
  },

  async getRule(ruleId: string): Promise<AutomationRule> {
    return fetchApi<AutomationRule>(`/automations/${ruleId}`);
  },

  async createRule(payload: AutomationRuleCreate): Promise<AutomationRule> {
    return fetchApi<AutomationRule>('/automations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateRule(ruleId: string, payload: AutomationRuleUpdate): Promise<AutomationRule> {
    return fetchApi<AutomationRule>(`/automations/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async activateRule(ruleId: string): Promise<AutomationRule> {
    return fetchApi<AutomationRule>(`/automations/${ruleId}/activate`, {
      method: 'POST',
    });
  },

  async pauseRule(ruleId: string): Promise<AutomationRule> {
    return fetchApi<AutomationRule>(`/automations/${ruleId}/pause`, {
      method: 'POST',
    });
  },

  async archiveRule(ruleId: string): Promise<AutomationRule> {
    return fetchApi<AutomationRule>(`/automations/${ruleId}/archive`, {
      method: 'POST',
    });
  },

  async deleteRule(ruleId: string): Promise<void> {
    return fetchApi<void>(`/automations/${ruleId}`, {
      method: 'DELETE',
    });
  },

  async getExecutions(params?: ExecutionQueryParams): Promise<AutomationExecution[]> {
    const query = new URLSearchParams();
    if (params?.rule_id) query.append('rule_id', params.rule_id);
    if (params?.status) query.append('status', params.status);
    if (params?.event_type) query.append('event_type', params.event_type);
    const qStr = query.toString();
    return fetchApi<AutomationExecution[]>(`/automations/executions${qStr ? `?${qStr}` : ''}`);
  },

  async getExecutionDetail(executionId: string): Promise<AutomationExecution> {
    return fetchApi<AutomationExecution>(`/automations/executions/${executionId}`);
  },

  async retryExecution(executionId: string): Promise<AutomationExecution> {
    return fetchApi<AutomationExecution>(`/automations/executions/${executionId}/retry`, {
      method: 'POST',
    });
  },

  async getAnalyticsSummary(): Promise<AutomationAnalyticsSummary> {
    return fetchApi<AutomationAnalyticsSummary>('/automations/analytics/summary');
  },

  async getAiRecommendations(): Promise<AIRuleRecommendation[]> {
    return fetchApi<AIRuleRecommendation[]>('/automations/ai-recommendations');
  },
};
