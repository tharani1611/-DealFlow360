import { fetchApi } from './apiClient';
import { Deal, DealCreate, DealUpdate, DealStage } from '../types';

export interface PipelineStageSummary {
  stage: DealStage;
  label: string;
  count: number;
  total_value: number;
  deals: Deal[];
}

export const dealApi = {
  async getDeals(params?: { customer_id?: string; stage?: DealStage; status?: string; search?: string; limit?: number; offset?: number }): Promise<Deal[]> {
    const query = new URLSearchParams();
    if (params?.customer_id) query.append('customer_id', params.customer_id);
    if (params?.stage) query.append('stage', params.stage);
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const queryStr = query.toString();
    return fetchApi<Deal[]>(`/deals${queryStr ? `?${queryStr}` : ''}`);
  },

  async getDeal(id: string): Promise<Deal> {
    return fetchApi<Deal>(`/deals/${id}`);
  },

  async createDeal(payload: DealCreate): Promise<Deal> {
    return fetchApi<Deal>('/deals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateDeal(id: string, payload: DealUpdate): Promise<Deal> {
    return fetchApi<Deal>(`/deals/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async transitionDealStage(id: string, stage: DealStage, lost_reason?: string): Promise<Deal> {
    const payload: DealUpdate = { stage };
    if (lost_reason) payload.lost_reason = lost_reason;

    return fetchApi<Deal>(`/deals/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
};
