import { fetchApi } from './apiClient';
import { Contact, ContactCreate, ContactUpdate } from '../types';

export const contactApi = {
  async getContacts(params?: { customer_id?: string; search?: string; limit?: number; offset?: number }): Promise<Contact[]> {
    const query = new URLSearchParams();
    if (params?.customer_id) query.append('customer_id', params.customer_id);
    if (params?.search) query.append('search', params.search);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const queryStr = query.toString();
    return fetchApi<Contact[]>(`/contacts${queryStr ? `?${queryStr}` : ''}`);
  },

  async getContact(id: string): Promise<Contact> {
    return fetchApi<Contact>(`/contacts/${id}`);
  },

  async createContact(payload: ContactCreate): Promise<Contact> {
    return fetchApi<Contact>('/contacts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateContact(id: string, payload: ContactUpdate): Promise<Contact> {
    return fetchApi<Contact>(`/contacts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async deleteContact(id: string): Promise<void> {
    return fetchApi<void>(`/contacts/${id}`, {
      method: 'DELETE',
    });
  },
};
