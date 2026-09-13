const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function req(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    credentials: 'include',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new Error((data && data.detail) || res.statusText)
  return data
}

export const api = {
  get: (p) => req('GET', p),
  post: (p, b) => req('POST', p, b),
  put: (p, b) => req('PUT', p, b),
  del: (p) => req('DELETE', p),

  profiles: () => req('GET', '/profiles'),
  login: (userId, password) => req('POST', '/auth/login', { user_id: userId, password }),
  logout: () => req('POST', '/auth/logout'),
  whoami: () => req('GET', '/whoami'),

  // self-service
  changePassword: (current_password, new_password) => req('POST', '/me/password', { current_password, new_password }),
  setAvatar: (avatar) => req('PUT', '/me/avatar', { avatar }),

  // admin
  listUsers: () => req('GET', '/users'),
  createUser: (body) => req('POST', '/users', body),
  resetPassword: (id, new_password) => req('POST', `/users/${id}/reset-password`, { new_password }),
  deleteUser: (id) => req('DELETE', `/users/${id}`),

  funds: (includeInactive = false) => req('GET', `/funds?include_inactive=${includeInactive}`),
  labels: () => req('GET', '/labels'),
  groups: () => req('GET', '/groups'),
  overview: (month) => req('GET', `/overview?month=${month}`),
  fundDetail: (id, month) => req('GET', `/funds/${id}/detail?month=${month}`),
  balanceSuggestions: (id, month) => req('GET', `/funds/${id}/balance-suggestions?month=${month}`),
  budget: (id, month) => req('GET', `/budgets/${id}?month=${month}`),
  setBudget: (id, month, body) => req('PUT', `/budgets/${id}?month=${month}`, body),
  closeMonth: (month) => req('POST', `/months/${month}/close`),
  transfer: (body) => req('POST', '/transfers', body),
  analysis: (qs) => req('GET', `/analysis?${qs}`),
  heatmap: (months) => {
    const p = new URLSearchParams()
    months.forEach((m) => p.append('months', m))
    return req('GET', `/heatmap?${p.toString()}`)
  },
  history: () => req('GET', '/history'),
  audit: (month) => req('GET', `/audit?month=${month}`),
  backup: () => req('POST', '/backup/export'),
}
