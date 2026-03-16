// API client: all requests send cookies (credentials: 'include').
// On 401: tries POST /auth/refresh once, then retries the original request.
// If refresh fails: calls setSessionExpiredHandler (e.g. redirect to login) and throws.

const API_BASE = '/api';

let onSessionExpired = null;

export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler;
}

// Internal: fetch with cookies; on 401 retry once after refresh, else call session-expired handler
async function request(path, options = {}, retried = false) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (res.status === 401 && !retried) {
    const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (refreshRes.ok) {
      return request(path, options, true);
    }
    if (onSessionExpired) onSessionExpired();
    throw new Error('SESSION_EXPIRED');
  }

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) return null;
  return res.json();
}

export const apiClient = {
  login(payload) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  register(payload) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  me() {
    return request('/auth/me');
  },

  logout() {
    return request('/auth/logout', { method: 'POST' });
  },

  getDashboardMetrics() {
    return request('/dashboard/metrics');
  },

  getDashboardStats() {
    return request('/dashboard/stats');
  },

  getDashboardAiReport() {
    return request('/dashboard/ai-report');
  },

  getCompaniesTop() {
    return request('/companies/top');
  },

  getTechnologiesTrending() {
    return request('/companies/technologies/trending');
  },

  getCompaniesEnriched() {
    return request('/companies/enriched');
  },

  getCompanies(search, tech, score) {
    const q = new URLSearchParams();
    if (search) q.set('search', search);
    if (tech) q.set('tech', tech);
    if (score) q.set('score', score);
    const suffix = q.toString() ? '?' + q.toString() : '';
    return request('/companies/enriched' + suffix);
  },

  runScraping(payload) {
    return request('/scraping/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getEmailPipeline() {
    return request('/emails/pipeline');
  },

  generateEmailTemplate(payload) {
    return request('/emails/template/ai', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  sendBulkEmails(payload) {
    return request('/emails/send-bulk', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getProfile() {
    return request('/profile/me');
  },

  updateProfile(payload) {
    return request('/profile/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  updateSmtpConfig(payload) {
    return request('/profile/smtp', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  testSmtp() {
    return request('/profile/smtp/test', { method: 'POST' });
  },
};
