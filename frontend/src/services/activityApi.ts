import { fetchApi } from './apiClient';
import { Activity, ActivityCreate, ActivityUpdate, ActivityStatus } from '../types';

export const activityApi = {
  async getActivities(params?: { customer_id?: string; deal_id?: string; quotation_id?: string; status?: ActivityStatus; search?: string; limit?: number; offset?: number }): Promise<Activity[]> {
    const query = new URLSearchParams();
    if (params?.customer_id) query.append('customer_id', params.customer_id);
    if (params?.deal_id) query.append('deal_id', params.deal_id);
    if (params?.quotation_id) query.append('quotation_id', params.quotation_id);
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const queryStr = query.toString();
    return fetchApi<Activity[]>(`/activities${queryStr ? `?${queryStr}` : ''}`);
  },

  async getCustomerActivities(customerId: string, limit: number = 20): Promise<Activity[]> {
    return fetchApi<Activity[]>(`/customers/${customerId}/activities?limit=${limit}`);
  },

  async getDealActivities(dealId: string, limit: number = 20): Promise<Activity[]> {
    return fetchApi<Activity[]>(`/deals/${dealId}/activities?limit=${limit}`);
  },

  async getActivity(id: string): Promise<Activity> {
    return fetchApi<Activity>(`/activities/${id}`);
  },

  async createActivity(payload: ActivityCreate): Promise<Activity> {
    return fetchApi<Activity>('/activities', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateActivity(id: string, payload: ActivityUpdate): Promise<Activity> {
    return fetchApi<Activity>(`/activities/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async completeActivity(id: string): Promise<Activity> {
    return fetchApi<Activity>(`/activities/${id}/complete`, {
      method: 'POST',
    });
  },

  async cancelActivity(id: string): Promise<Activity> {
    return fetchApi<Activity>(`/activities/${id}/cancel`, {
      method: 'POST',
    });
  },
};
