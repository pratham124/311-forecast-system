const trimTrailingSlash = (value: string) => value.replace(/\/$/, '');

export const env = {
  apiBaseUrl: trimTrailingSlash(import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'),
  dashboardDefaultProduct: (import.meta.env.VITE_DASHBOARD_DEFAULT_PRODUCT ?? 'daily_1_day') as 'daily_1_day' | 'weekly_7_day',
  renderEventSubmission: (import.meta.env.VITE_RENDER_EVENT_SUBMISSION ?? 'enabled') as 'enabled' | 'disabled',
};
