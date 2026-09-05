import { fetchApi } from './apiClient';
import { Customer, CustomerCreate, CustomerUpdate } from '../types';

export const customerApi = {
  async getCustomers(params?: { search?: string; is_active?: boolean; limit?: number; offset?: number }): Promise<Customer[]> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const queryStr = query.toString();
    return fetchApi<Customer[]>(`/customers${queryStr ? `?${queryStr}` : ''}`);
  },

  async getCustomer(id: string): Promise<Customer> {
    return fetchApi<Customer>(`/customers/${id}`);
  },

  async createCustomer(payload: CustomerCreate): Promise<Customer> {
    return fetchApi<Customer>('/customers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateCustomer(id: string, payload: CustomerUpdate): Promise<Customer> {
    return fetchApi<Customer>(`/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async deleteCustomer(id: string): Promise<void> {
    return fetchApi<void>(`/customers/${id}`, {
      method: 'DELETE',
    });
  },
};
