import {
  PortalTokenResponse,
  PortalUserResponse,
  PortalQuotationListItemResponse,
  PortalQuotationDetailResponse,
  PortalActionResponse,
  ChangeRequestCreate,
  ChangeRequest,
  LineComment,
  LineCommentCreate
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function fetchPortalApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('portal_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Portal request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data.error && data.error.message) {
        message = data.error.message;
      } else if (data.detail) {
        message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {}

    if (response.status === 401 && !endpoint.includes('/portal/auth/login')) {
      localStorage.removeItem('portal_token');
      if (window.location.pathname !== '/portal/login') {
        window.location.href = '/portal/login';
      }
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const portalApi = {
  login: async (email: string, password: string): Promise<PortalTokenResponse> => {
    const res = await fetchPortalApi<PortalTokenResponse>('/portal/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) {
      localStorage.setItem('portal_token', res.access_token);
    }
    return res;
  },

  getMe: async (): Promise<PortalUserResponse> => {
    return fetchPortalApi<PortalUserResponse>('/portal/auth/me');
  },

  logout: (): void => {
    localStorage.removeItem('portal_token');
  },

  getQuotations: async (): Promise<PortalQuotationListItemResponse[]> => {
    return fetchPortalApi<PortalQuotationListItemResponse[]>('/portal/quotations');
  },

  getQuotationDetail: async (quotationId: string): Promise<PortalQuotationDetailResponse> => {
    return fetchPortalApi<PortalQuotationDetailResponse>(`/portal/quotations/${quotationId}`);
  },

  acceptQuotation: async (quotationId: string, reason?: string): Promise<PortalActionResponse> => {
    return fetchPortalApi<PortalActionResponse>(`/portal/quotations/${quotationId}/accept`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  rejectQuotation: async (quotationId: string, reason?: string): Promise<PortalActionResponse> => {
    return fetchPortalApi<PortalActionResponse>(`/portal/quotations/${quotationId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  createChangeRequest: async (quotationId: string, payload: ChangeRequestCreate): Promise<ChangeRequest> => {
    return fetchPortalApi<ChangeRequest>(`/portal/quotations/${quotationId}/change-requests`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getComments: async (quotationId: string): Promise<LineComment[]> => {
    return fetchPortalApi<LineComment[]>(`/portal/quotations/${quotationId}/comments`);
  },

  createComment: async (quotationId: string, payload: LineCommentCreate): Promise<LineComment> => {
    return fetchPortalApi<LineComment>(`/portal/quotations/${quotationId}/comments`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
