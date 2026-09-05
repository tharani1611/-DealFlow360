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

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err: any) {
    throw {
      message: 'Network error: Server is unreachable or offline. Please check your connection.',
      status_code: 0,
      details: { originalError: err.message },
    } as ApiError;
  }

  if (response.status === 204) { // No Content
    return {} as T;
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    let details: Record<string, any> | undefined = undefined;

    try {
      const data = await response.json();
      if (data.error && typeof data.error === 'object') {
        message = data.error.message || message;
        details = data.error.details;
      } else if (data.detail) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
        }
      }
    } catch {
      // Raw text fallback
    }

    // Standardized status code translation
    if (response.status === 401 && !endpoint.includes('/auth/login')) {
      localStorage.removeItem('access_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      message = 'Session expired or unauthorized. Please log in again.';
    } else if (response.status === 403) {
      message = message || 'Access Restricted: You do not have permission to perform this action.';
    } else if (response.status === 404) {
      message = message || 'Requested resource was not found.';
    } else if (response.status === 409) {
      message = message || 'Conflict: Record already exists or state transition is invalid.';
    } else if (response.status === 422) {
      message = message || 'Validation Error: Unprocessable request data.';
    } else if (response.status === 429) {
      message = 'Rate Limit Exceeded: Too many requests. Please wait a moment.';
    } else if (response.status >= 500) {
      message = 'Internal Server Error: Something went wrong on the server.';
    }

    const errorData: ApiError = {
      message,
      status_code: response.status,
      details,
    };

    throw errorData;
  }

  return response.json() as Promise<T>;
}
