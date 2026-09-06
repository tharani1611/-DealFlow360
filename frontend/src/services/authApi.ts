import { fetchApi } from './apiClient';
import { AuthTokens, User } from '../types';

export const authApi = {
  async login(payload: { organization_slug: string; email: string; password: string }): Promise<AuthTokens> {
    return fetchApi<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async register(payload: {
    organization_name?: string;
    organization_slug: string;
    email: string;
    password: string;
    role?: string;
    full_name?: string;
  }): Promise<AuthTokens> {
    return fetchApi<AuthTokens>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getMe(): Promise<User> {
    return fetchApi<User>('/auth/me');
  },
};
