import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

const api = axios.create({
  baseURL: BASE,
  timeout: 60000, // keep the 60s timeout
  headers: { "Content-Type": "application/json" },
});

// Token interceptor – works with either storage shape
api.interceptors.request.use((config) => {
  if (typeof window === "undefined") return config;
  
  let token = null;
  try {
    // Try direct token first
    token = localStorage.getItem("wakili_token");
    if (!token) {
      const store = JSON.parse(localStorage.getItem("wakili-store") || "{}");
      token = store?.state?.token;
    }
  } catch { /* ignore parse errors */ }
  
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 401 redirect
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("wakili_token");
      localStorage.removeItem("wakili-store");
      window.location.href = "/auth/login";
    }
    return Promise.reject(err);
  }
);

// ─── Typed APIs ─────────────────────────────────
export const documentsApi = {
  list: () => api.get("/documents"),          // adjust if backend expects /documents/documents
  get: (id: number) => api.get(`/documents/${id}`),
  delete: (id: number) => api.delete(`/documents/${id}`),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export const askApi = {
  ask: (question: string, documentId?: number, language?: string, history?: HistoryEntry[]) =>
    api.post("/ask", {
      question,
      document_id: documentId ?? null,
      language: language ?? null,
      conversation_history: history ?? [],
    }),
};

export const metricsApi = {
  get: () => api.get("/metrics"),
};

export const authApi = {
  register: (data: { email: string; full_name: string; password: string; preferred_language: string }) =>
    api.post("/auth/register", data),
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),
  // Provide optional token for immediate use after login
  me: (token?: string) =>
    token
      ? api.get("/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      : api.get("/auth/me"),
};

// Re-export types
export interface HistoryEntry {
  role: "user" | "assistant";
  content: string;
}

export default api;