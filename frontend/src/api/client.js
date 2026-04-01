import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function apiRequest(path, options = {}) {
  const method = options.method || "GET";
  const headers = options.headers || {};
  let data;

  if (typeof options.body === "string") {
    try {
      data = JSON.parse(options.body);
    } catch (error) {
      console.warn("Failed to parse request body as JSON.", error);
      data = undefined;
    }
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
