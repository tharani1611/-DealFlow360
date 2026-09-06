import { fetchApi } from './apiClient';
import {
  DiscountPolicy,
  DiscountPolicyCreate,
  ApprovalRule,
  ApprovalRuleCreate,
  QuotationApproval,
  ApprovalDecisionRequest,
  CommercialGovernanceSummaryResponse,
} from '../types';

export const commercialGovernanceApi = {
  // Discount Policies
  async getDiscountPolicies(params?: { scope?: string; is_active?: boolean }): Promise<DiscountPolicy[]> {
    const query = new URLSearchParams();
    if (params?.scope) query.append('scope', params.scope);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    const qStr = query.toString();
    return fetchApi<DiscountPolicy[]>(`/discount-governance/policies${qStr ? `?${qStr}` : ''}`);
  },

  async createDiscountPolicy(payload: DiscountPolicyCreate): Promise<DiscountPolicy> {
    return fetchApi<DiscountPolicy>('/discount-governance/policies', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteDiscountPolicy(policyId: string): Promise<void> {
    return fetchApi<void>(`/discount-governance/policies/${policyId}`, {
      method: 'DELETE',
    });
  },

  // Approval Rules
  async getApprovalRules(params?: { is_active?: boolean }): Promise<ApprovalRule[]> {
    const query = new URLSearchParams();
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    const qStr = query.toString();
    return fetchApi<ApprovalRule[]>(`/approvals/rules${qStr ? `?${qStr}` : ''}`);
  },

  async createApprovalRule(payload: ApprovalRuleCreate): Promise<ApprovalRule> {
    return fetchApi<ApprovalRule>('/approvals/rules', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteApprovalRule(ruleId: string): Promise<void> {
    return fetchApi<void>(`/approvals/rules/${ruleId}`, {
      method: 'DELETE',
    });
  },

  // Quotation Commercial Governance Summary
  async getQuotationGovernanceSummary(quotationId: string): Promise<CommercialGovernanceSummaryResponse> {
    return fetchApi<CommercialGovernanceSummaryResponse>(`/quotations/${quotationId}/governance`);
  },

  // Submit Approval Decision
  async submitApprovalDecision(quotationId: string, payload: ApprovalDecisionRequest): Promise<QuotationApproval> {
    return fetchApi<QuotationApproval>(`/approvals/quotations/${quotationId}/decision`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // List Approval Inbox
  async getApprovalInbox(statusFilter?: string): Promise<QuotationApproval[]> {
    const query = statusFilter ? `?status=${statusFilter}` : '';
    return fetchApi<QuotationApproval[]>(`/approvals/inbox${query}`);
  },
};
