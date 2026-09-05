import { fetchApi } from './apiClient';
import {
  DealHealthResponse,
  CustomerEngagementResponse,
  SalesBriefingResponse,
  DashboardIntelligenceResponse,
  AttentionCenterResponse,
  AlertsResponse,
  ActivityProductivityMetrics,
  CustomerProductRecommendationsResponse,
} from '../types';

export const intelligenceApi = {
  async getDealHealth(dealId: string): Promise<DealHealthResponse> {
    return fetchApi<DealHealthResponse>(`/intelligence/deals/${dealId}/health`);
  },

  async getCustomerEngagement(customerId: string): Promise<CustomerEngagementResponse> {
    return fetchApi<CustomerEngagementResponse>(`/intelligence/customers/${customerId}/engagement`);
  },

  async getCustomerProductRecommendations(customerId: string): Promise<CustomerProductRecommendationsResponse> {
    return fetchApi<CustomerProductRecommendationsResponse>(`/intelligence/customers/${customerId}/product-recommendations`);
  },

  async getSalesBriefing(customerId: string): Promise<SalesBriefingResponse> {
    return fetchApi<SalesBriefingResponse>(`/intelligence/customers/${customerId}/briefing`);
  },

  async getDashboardIntelligence(): Promise<DashboardIntelligenceResponse> {
    return fetchApi<DashboardIntelligenceResponse>('/intelligence/dashboard');
  },

  async getAttention(): Promise<AttentionCenterResponse> {
    return fetchApi<AttentionCenterResponse>('/intelligence/attention');
  },

  async getAlerts(): Promise<AlertsResponse> {
    return fetchApi<AlertsResponse>('/intelligence/alerts');
  },

  async getActivityProductivity(): Promise<ActivityProductivityMetrics> {
    return fetchApi<ActivityProductivityMetrics>('/intelligence/activity-productivity');
  },
};
