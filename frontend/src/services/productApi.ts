import { fetchApi } from './apiClient';
import { Product, ProductCreate, ProductUpdate } from '../types';

export const productApi = {
  async getProducts(params?: { search?: string; is_active?: boolean; limit?: number; offset?: number }): Promise<Product[]> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const queryStr = query.toString();
    return fetchApi<Product[]>(`/products${queryStr ? `?${queryStr}` : ''}`);
  },

  async getProduct(id: string): Promise<Product> {
    return fetchApi<Product>(`/products/${id}`);
  },

  async createProduct(payload: ProductCreate): Promise<Product> {
    return fetchApi<Product>('/products', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateProduct(id: string, payload: ProductUpdate): Promise<Product> {
    return fetchApi<Product>(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async deleteProduct(id: string): Promise<void> {
    return fetchApi<void>(`/products/${id}`, {
      method: 'DELETE',
    });
  },
};
