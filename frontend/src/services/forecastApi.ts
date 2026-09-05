import { fetchApi } from './apiClient';
import { RevenueForecastResponse, ForecastExplanationResponse } from '../types';

export interface ForecastQueryParams {
  period?: string;
  stage?: string;
  forecast_category?: string;
  customer_id?: string;
}

export const forecastApi = {
  async getForecast(params?: ForecastQueryParams): Promise<RevenueForecastResponse> {
    const query = new URLSearchParams();
    if (params?.period) query.append('period', params.period);
    if (params?.stage) query.append('stage', params.stage);
    if (params?.forecast_category) query.append('forecast_category', params.forecast_category);
    if (params?.customer_id) query.append('customer_id', params.customer_id);

    const queryString = query.toString();
    const endpoint = `/intelligence/forecast${queryString ? `?${queryString}` : ''}`;
    return fetchApi<RevenueForecastResponse>(endpoint);
  },

  async getForecastExplanation(): Promise<ForecastExplanationResponse> {
    return fetchApi<ForecastExplanationResponse>('/intelligence/forecast/explain');
  },
};
