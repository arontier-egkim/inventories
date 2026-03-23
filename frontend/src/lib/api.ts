const API_BASE = "http://localhost:8000/api/v1";

async function fetchAPI(path: string, options?: RequestInit) {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options?.body instanceof FormData))
    headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error?.message || res.statusText);
  }

  const ct = res.headers.get("content-type");
  if (ct?.includes("application/json")) return res.json();
  return res;
}

export const api = {
  get: (path: string) => fetchAPI(path),
  post: (path: string, body?: unknown) =>
    fetchAPI(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: (path: string, body?: unknown) =>
    fetchAPI(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: (path: string) => fetchAPI(path, { method: "DELETE" }),
};
