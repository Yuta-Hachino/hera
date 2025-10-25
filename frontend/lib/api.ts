import {
  SessionResponse,
  MessageResponse,
  StatusResponse,
  CompleteResponse,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
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

export async function createSession(): Promise<SessionResponse> {
  return fetchApi<SessionResponse>('/api/sessions', {
    method: 'POST',
  });
}

export async function sendMessage(
  sessionId: string,
  message: string
): Promise<MessageResponse> {
  return fetchApi<MessageResponse>(`/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function getSessionStatus(
  sessionId: string
): Promise<StatusResponse> {
  return fetchApi<StatusResponse>(`/api/sessions/${sessionId}/status`);
}

export async function completeSession(
  sessionId: string
): Promise<CompleteResponse> {
  return fetchApi<CompleteResponse>(`/api/sessions/${sessionId}/complete`, {
    method: 'POST',
  });
}

export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/api/health');
}
