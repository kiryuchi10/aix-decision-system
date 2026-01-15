/**
 * Centralized API Client
 * Supports real server and mock switching via environment variables
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') as string;
const USE_MOCKS = (import.meta.env.VITE_USE_MOCKS === 'true') as boolean;

export type ApiError = {
  status: number;
  message: string;
  details?: unknown;
};

async function parseJsonSafe(res: Response) {
  const text = await res.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return text;
  }
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function apiGet<T>(path: string): Promise<T> {
  if (USE_MOCKS) {
    // TODO: Implement MSW handlers
    throw new Error('Mock mode not yet implemented');
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    credentials: 'include',
    headers: await getAuthHeaders(),
  });

  if (!res.ok) {
    const details = await parseJsonSafe(res);
    throw {
      status: res.status,
      message: `GET ${path} failed`,
      details,
    } as ApiError;
  }
  return (await res.json()) as T;
}

export async function apiPost<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  if (USE_MOCKS) {
    throw new Error('Mock mode not yet implemented');
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: await getAuthHeaders(),
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const details = await parseJsonSafe(res);
    throw {
      status: res.status,
      message: `POST ${path} failed`,
      details,
    } as ApiError;
  }
  return (await res.json()) as TRes;
}

export async function apiPut<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  if (USE_MOCKS) {
    throw new Error('Mock mode not yet implemented');
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PUT',
    credentials: 'include',
    headers: await getAuthHeaders(),
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const details = await parseJsonSafe(res);
    throw {
      status: res.status,
      message: `PUT ${path} failed`,
      details,
    } as ApiError;
  }
  return (await res.json()) as TRes;
}

export async function apiDelete<T>(path: string): Promise<T> {
  if (USE_MOCKS) {
    throw new Error('Mock mode not yet implemented');
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: await getAuthHeaders(),
  });

  if (!res.ok) {
    const details = await parseJsonSafe(res);
    throw {
      status: res.status,
      message: `DELETE ${path} failed`,
      details,
    } as ApiError;
  }
  return (await res.json()) as T;
}
