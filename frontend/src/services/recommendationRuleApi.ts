import { fetchApi } from './apiClient';
import {
  ProductRecommendationRule,
  ProductRecommendationRuleCreate,
} from '../types';

export const recommendationRuleApi = {
  async getRules(params?: {
    rule_type?: string;
    source_product_id?: string;
    target_product_id?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<ProductRecommendationRule[]> {
    const query = new URLSearchParams();
    if (params?.rule_type) query.append('rule_type', params.rule_type);
    if (params?.source_product_id) query.append('source_product_id', params.source_product_id);
    if (params?.target_product_id) query.append('target_product_id', params.target_product_id);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));

    const queryString = query.toString();
    const endpoint = `/product-recommendation-rules${queryString ? `?${queryString}` : ''}`;
    return fetchApi<ProductRecommendationRule[]>(endpoint);
  },

  async getRule(id: string): Promise<ProductRecommendationRule> {
    return fetchApi<ProductRecommendationRule>(`/product-recommendation-rules/${id}`);
  },

  async createRule(payload: ProductRecommendationRuleCreate): Promise<ProductRecommendationRule> {
    return fetchApi<ProductRecommendationRule>('/product-recommendation-rules', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateRule(id: string, payload: Partial<ProductRecommendationRuleCreate>): Promise<ProductRecommendationRule> {
    return fetchApi<ProductRecommendationRule>(`/product-recommendation-rules/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async deleteRule(id: string): Promise<void> {
    return fetchApi<void>(`/product-recommendation-rules/${id}`, {
      method: 'DELETE',
    });
  },
};
