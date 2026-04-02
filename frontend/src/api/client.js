import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config || {};
    config.__retryCount = config.__retryCount || 0;
    const shouldRetry =
      (!error.response || error.response.status >= 500) && config.__retryCount < 2;

    if (!shouldRetry) {
      throw error;
    }

    config.__retryCount += 1;
    await new Promise((resolve) => setTimeout(resolve, 300 * config.__retryCount));
    return apiClient.request(config);
  }
);

export async function apiRequest(path, options = {}) {
  const method = options.method || "GET";
  const headers = options.headers || {};
  let data;
  const body = options.body;

  if (typeof body === "string") {
    try {
      data = JSON.parse(body);
    } catch (error) {
      console.warn("Failed to parse request body as JSON.", error);
      data = undefined;
    }
  } else if (
    body &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof URLSearchParams) &&
    !(body instanceof Blob)
  ) {
    data = body;
  }

  const response = await apiClient.request({
    url: path,
    method,
    headers,
    data,
  });

  return response.data;
}

export function withAuth(token) {
  return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
}

export function getMonitoringWebSocketUrl(token) {
  const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
  const websocketBase = apiBase.replace(/^http/i, "ws");
  const trimmedBase = websocketBase.endsWith("/") ? websocketBase.slice(0, -1) : websocketBase;
  return `${trimmedBase}/admin/monitoring/ws?token=${encodeURIComponent(token || "")}`;
}
