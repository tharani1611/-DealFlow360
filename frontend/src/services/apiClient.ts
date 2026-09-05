export interface ApiError {
  message: string;
  status_code: number;
  details?: Record<string, any>;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token');
  
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

  if (response.status === 24) { // No Content
    return {} as T;
  }

  if (!response.ok) {
    let errorData: ApiError = {
      message: `Request failed with status ${response.status}`,
      status_code: response.status,
    };
    try {
      const data = await response.json();
      if (data.error && typeof data.error === 'object') {
        errorData = {
          message: data.error.message || 'An error occurred',
          status_code: data.error.status_code || response.status,
          details: data.error.details,
        };
      } else if (data.detail) {
        if (typeof data.detail === 'string') {
          errorData.message = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorData.message = data.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
        }
      }
    } catch {
      // Fallback response parsing
    }

    if (response.status === 401 && !endpoint.includes('/auth/login')) {
      localStorage.removeItem('access_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    throw errorData;
  }

  return response.json() as Promise<T>;
}
