import { fetchApi } from './apiClient';
import { AuthTokens, User } from '../types';

export const authApi = {
  async login(formData: URLSearchParams): Promise<AuthTokens> {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      let message = 'Invalid login credentials';
      try {
        const data = await response.json();
        if (data.error?.message) message = data.error.message;
        else if (data.detail) message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } catch {
        // Fallback
      }
      throw { message, status_code: response.status };
    }

    return response.json();
  },

  async register(payload: { organization_name: string; organization_slug: string; email: string; password: string; full_name?: string }): Promise<AuthTokens> {
    return fetchApi<AuthTokens>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getMe(): Promise<User> {
    return fetchApi<User>('/auth/me');
  },
};
