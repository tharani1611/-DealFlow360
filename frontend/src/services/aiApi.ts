import { fetchApi } from './apiClient';
import {
  CustomerSummaryResponse,
  DealAnalysisResponse,
  NextActionResponse,
  ActivityInsightResponse,
  AssistantResponse,
} from '../types';

export const aiApi = {
  async getCustomerSummary(customerId: string): Promise<CustomerSummaryResponse> {
    return fetchApi<CustomerSummaryResponse>(`/ai/customers/${customerId}/summary`, {
      method: 'POST',
    });
  },

  async getDealAnalysis(dealId: string): Promise<DealAnalysisResponse> {
    return fetchApi<DealAnalysisResponse>(`/ai/deals/${dealId}/analysis`, {
      method: 'POST',
    });
  },

  async getNextAction(dealId: string): Promise<NextActionResponse> {
    return fetchApi<NextActionResponse>(`/ai/deals/${dealId}/next-action`, {
      method: 'POST',
    });
  },

  async getActivityInsights(dealId: string): Promise<ActivityInsightResponse> {
    return fetchApi<ActivityInsightResponse>(`/ai/deals/${dealId}/activity-insights`, {
      method: 'POST',
    });
  },

  async askAssistant(question: string): Promise<AssistantResponse> {
    return fetchApi<AssistantResponse>('/ai/assistant', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
  },
};
