import { fetchApi } from './apiClient';
import { Quotation, QuotationCreate, QuotationUpdate, QuotationStateHistoryItem, QuotationTransitionRequest } from '../types';

export const quotationApi = {
  async getQuotations(params?: { customer_id?: string; status?: string; search?: string; limit?: number; offset?: number }): Promise<Quotation[]> {
    const query = new URLSearchParams();
    if (params?.customer_id) query.append('customer_id', params.customer_id);
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const queryStr = query.toString();
    return fetchApi<Quotation[]>(`/quotations${queryStr ? `?${queryStr}` : ''}`);
  },

  async getQuotation(id: string): Promise<Quotation> {
    return fetchApi<Quotation>(`/quotations/${id}`);
  },

  async createQuotation(payload: QuotationCreate): Promise<Quotation> {
    return fetchApi<Quotation>('/quotations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateQuotation(id: string, payload: QuotationUpdate): Promise<Quotation> {
    return fetchApi<Quotation>(`/quotations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async transitionQuotation(id: string, payload: QuotationTransitionRequest): Promise<Quotation> {
    return fetchApi<Quotation>(`/quotations/${id}/transition`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getQuotationHistory(id: string): Promise<QuotationStateHistoryItem[]> {
    return fetchApi<QuotationStateHistoryItem[]>(`/quotations/${id}/history`);
  },
};
