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
  Customer360Intelligence,
  Product360Intelligence,
  DealHealthSnapshot,
  StalledQuotesResponse,
  DiscountAnomaliesResponse,
  DeliverySlippageResponse,
  NudgesResponse,
  Nudge,
  ExecutiveReportSummaryResponse,
  ExecutiveAnalyticsResponse,
} from '../types';

export const intelligenceApi = {
  async getDealHealth(dealId: string): Promise<DealHealthResponse> {
    return fetchApi<DealHealthResponse>(`/intelligence/deals/${dealId}/health`);
  },

  async evaluateDealHealth(dealId: string): Promise<DealHealthSnapshot> {
    return fetchApi<DealHealthSnapshot>(`/intelligence/deals/${dealId}/health-snapshot`, {
      method: 'POST',
    });
  },

  async getCustomerEngagement(customerId: string): Promise<CustomerEngagementResponse> {
    return fetchApi<CustomerEngagementResponse>(`/intelligence/customers/${customerId}/engagement`);
  },

  async getCustomer360(customerId: string): Promise<Customer360Intelligence> {
    return fetchApi<Customer360Intelligence>(`/intelligence/customers/${customerId}/360`);
  },

  async getProduct360(productId: string): Promise<Product360Intelligence> {
    return fetchApi<Product360Intelligence>(`/intelligence/products/${productId}/360`);
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

  async getStalledQuotes(daysThreshold: number = 14): Promise<StalledQuotesResponse> {
    return fetchApi<StalledQuotesResponse>(`/intelligence/monitoring/stalled-quotes?days_threshold=${daysThreshold}`);
  },

  async getDiscountAnomalies(): Promise<DiscountAnomaliesResponse> {
    return fetchApi<DiscountAnomaliesResponse>('/intelligence/monitoring/discount-anomalies');
  },

  async getDeliverySlippage(): Promise<DeliverySlippageResponse> {
    return fetchApi<DeliverySlippageResponse>('/intelligence/monitoring/delivery-slippage');
  },

  async getNudges(statusFilter?: string): Promise<NudgesResponse> {
    const query = statusFilter ? `?status_filter=${statusFilter}` : '';
    return fetchApi<NudgesResponse>(`/intelligence/nudges${query}`);
  },

  async transitionNudgeStatus(nudgeId: string, targetStatus: string, notes?: string): Promise<Nudge> {
    return fetchApi<Nudge>(`/intelligence/nudges/${nudgeId}/transition`, {
      method: 'POST',
      body: JSON.stringify({ target_status: targetStatus, notes }),
    });
  },

  async getExecutiveReport(period: string = 'this_month'): Promise<ExecutiveReportSummaryResponse> {
    return fetchApi<ExecutiveReportSummaryResponse>(`/intelligence/reports/executive-summary?period=${period}`);
  },

  async getExecutiveAnalytics(period: string = 'this_month'): Promise<ExecutiveAnalyticsResponse> {
    return fetchApi<ExecutiveAnalyticsResponse>(`/intelligence/analytics/dashboard-executive?period=${period}`);
  },
};


