import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Separate instance for file uploads (multipart/form-data)
export const uploadApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
})

// API endpoints
export const apiEndpoints = {
  overview: () => api.get('/api/overview'),
  inventory: () => api.get('/api/inventory'),
  riskAlerts: () => api.get('/api/risk-alerts'),
  usageTrends: (ingredient?: string, period: string = 'monthly') => 
    api.get('/api/usage-trends', { params: { ingredient, period } }),
  forecast: (ingredient: string, daysAhead: number = 30, method: string = 'moving_average', includeSeasonality: boolean = true, includeHolidays: boolean = true) =>
    api.get('/api/forecast', { params: { ingredient, days_ahead: daysAhead, method, include_seasonality: includeSeasonality, include_holidays: includeHolidays } }),
  menuForecast: (ingredient: string, daysAhead: number = 30) =>
    api.get('/api/menu-forecast', { params: { ingredient, days_ahead: daysAhead } }),
  recipeMapper: () => api.get('/api/recipe-mapper'),
  shipments: () => api.get('/api/shipments'),
  costAnalysis: (periodDays: number = 30) =>
    api.get('/api/cost-analysis', { params: { period_days: periodDays } }),
  waste: (periodDays: number = 30) =>
    api.get('/api/waste', { params: { period_days: periodDays } }),
  storage: (daysAhead: number = 7) =>
    api.get('/api/storage', { params: { days_ahead: daysAhead } }),
  reorder: (includeSeasonality: boolean = true) =>
    api.get('/api/reorder', { params: { include_seasonality: includeSeasonality } }),
  simulate: (scenario: any) => api.post('/api/simulate', scenario),
  chat: (query: string) => api.post('/api/chat', { query }),
  clearChat: () => api.post('/api/chat/clear'),
  reload: () => api.post('/api/reload'),
  ingredients: () => api.get('/api/ingredients'),
  menuItems: () => api.get('/api/menu-items'),
  uploadData: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    // Don't set Content-Type header - let axios set it with boundary
    return uploadApi.post('/api/upload-data', formData)
  },
  uploadHistory: () => api.get('/api/upload-history'),
}

