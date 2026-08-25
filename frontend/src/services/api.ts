// Centralized API client for LAMS Backend

const getEnvApiUrl = (): string => {
  try {
    return (import.meta as unknown as { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL || 'https://lams-production-1a83.up.railway.app';
  } catch {
    return 'https://lams-production-1a83.up.railway.app';
  }
};

const VITE_API_URL = getEnvApiUrl();
export const BASE_URL = VITE_API_URL.endsWith('/api') ? VITE_API_URL : `${VITE_API_URL.replace(/\/$/, '')}/api`;

const TOKEN_KEY = 'lams_access_token';

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserMeResponse {
  id: string;
  name: string;
  email: string;
  role: string;
  state_id?: number;
  district_id?: number;
  is_active: boolean;
}

export const apiClient = async <T>(endpoint: string, options: RequestOptions = {}): Promise<T> => {
  const token = getToken();
  const headers: Record<string, string> = {
    ...options.headers,
  };

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  console.log("[LAMS API] authenticated request:", endpoint, Boolean(token));

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
    }
    let errorMessage = `API request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // JSON parsing fallback
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
};

export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    return apiClient<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  getMe: async (): Promise<UserMeResponse> => {
    return apiClient<UserMeResponse>('/auth/me');
  },
};
