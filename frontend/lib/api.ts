import {
  SessionResponse,
  MessageResponse,
  StatusResponse,
  CompleteResponse,
  FamilyMessageResponse,
  FamilyStatusResponse,
} from './types';
import { getAccessToken } from './firebase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

interface FetchApiOptions extends RequestInit {
  requireAuth?: boolean;
}

async function fetchApi<T>(
  endpoint: string,
  options?: FetchApiOptions
): Promise<T> {
  const { requireAuth = false, ...fetchOptions } = options || {};
  const url = `${API_URL}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions?.headers as Record<string, string>),
  };

  // 認証が必要な場合はJWTトークンを付与
  if (requireAuth) {
    const token = await getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.error || `HTTP Error ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new Error(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

export async function createSession(requireAuth: boolean = false): Promise<SessionResponse> {
  return fetchApi<SessionResponse>('/api/sessions', {
    method: 'POST',
    requireAuth,
  });
}

export async function sendMessage(
  sessionId: string,
  message: string,
  requireAuth: boolean = false
): Promise<MessageResponse> {
  return fetchApi<MessageResponse>(`/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
    requireAuth,
  });
}

export async function getSessionStatus(
  sessionId: string,
  requireAuth: boolean = false
): Promise<StatusResponse> {
  return fetchApi<StatusResponse>(`/api/sessions/${sessionId}/status`, {
    requireAuth,
  });
}

export async function completeSession(
  sessionId: string,
  requireAuth: boolean = false
): Promise<CompleteResponse> {
  return fetchApi<CompleteResponse>(`/api/sessions/${sessionId}/complete`, {
    method: 'POST',
    requireAuth,
  });
}

export async function getFamilyStatus(
  sessionId: string,
  requireAuth: boolean = false
): Promise<FamilyStatusResponse> {
  return fetchApi<FamilyStatusResponse>(`/api/sessions/${sessionId}/family/status`, {
    requireAuth,
  });
}

export async function sendFamilyMessage(
  sessionId: string,
  message: string,
  requireAuth: boolean = false
): Promise<FamilyMessageResponse> {
  return fetchApi<FamilyMessageResponse>(`/api/sessions/${sessionId}/family/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
    requireAuth,
  });
}

export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/api/health');
}
