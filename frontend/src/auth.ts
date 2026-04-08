const ACCESS_TOKEN_KEY = 'token';
const REFRESH_TOKEN_KEY = 'refresh';

type AuthListener = () => void;

const listeners = new Set<AuthListener>();

function notifyAuthChange() {
  listeners.forEach((listener) => listener());
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  notifyAuthChange();
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  notifyAuthChange();
}

export function subscribeAuthChange(listener: AuthListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

