const API_URL = import.meta.env.VITE_API_URL ?? "";

export async function apiFetch<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Ошибка запроса" }));
    throw new Error(body.detail ?? "Ошибка запроса");
  }
  return response.json() as Promise<T>;
}

export { API_URL };
