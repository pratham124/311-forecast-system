import { useEffect, useRef, useState, type RefObject } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import {
  createThresholdConfiguration,
  deleteThresholdConfiguration,
  fetchThresholdAlertConfigurations,
  fetchThresholdAlertEvents,
  fetchThresholdServiceCategories,
  updateThresholdConfiguration,
} from '../api/forecastAlerts';
import { fetchSurgeEvents } from '../api/surgeAlerts';
import { AlertDetailPanel, useAlertDetail } from '../features/alert-details';
import { SurgeAlertReview } from '../features/surge_alerts';
import type { AlertSummary } from '../types/alertDetails';
import type {
  ForecastWindowType,
  OverallDeliveryStatus,
  ThresholdAlertEventSummary,
  ThresholdConfiguration,
  ThresholdConfigurationWrite,
} from '../types/forecastAlerts';
import type { SurgeAlertEventSummary } from '../types/surgeAlerts';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);
const WRITER_ROLES = new Set(['OperationalManager']);
const FORECAST_WINDOW_OPTIONS: Array<{ value: ForecastWindowType; label: string }> = [
  { value: 'hourly', label: 'Hourly' },
  { value: 'daily', label: 'Daily' },
];

const STATUS_STYLES: Record<OverallDeliveryStatus, { bg: string; text: string; icon: string; label: string }> = {
  delivered: { bg: 'bg-emerald-50', text: 'text-emerald-700', icon: '✓', label: 'Delivered' },
  partial_delivery: { bg: 'bg-amber-50', text: 'text-amber-700', icon: '◐', label: 'Partial' },
  retry_pending: { bg: 'bg-sky-50', text: 'text-sky-700', icon: '↻', label: 'Retry Pending' },
  manual_review_required: { bg: 'bg-red-50', text: 'text-red-700', icon: '!', label: 'Review Required' },
};

function deliveryStatusStyle(status: OverallDeliveryStatus) {
  return STATUS_STYLES[status] ?? STATUS_STYLES.delivered;
}

function canReadAlerts(roles: string[]): boolean {
  return roles.some((role) => READER_ROLES.has(role));
}

function canWriteThresholds(roles: string[]): boolean {
  return roles.some((role) => WRITER_ROLES.has(role));
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function mergeServiceCategories(serviceCategories: string[], thresholds: ThresholdConfiguration[], selectedCategory: string): string[] {
  return [...new Set([...serviceCategories, ...thresholds.map((item) => item.serviceCategory), selectedCategory].filter(Boolean))].sort();
}

function toThresholdAlertSummary(item: ThresholdAlertEventSummary): AlertSummary {
  return {
    alertSource: 'threshold_alert',
    alertId: item.notificationEventId,
    sourceLabel: 'Threshold',
    serviceCategory: item.serviceCategory,
    createdAt: item.createdAt,
    windowStart: item.forecastWindowStart,
    windowEnd: item.forecastWindowEnd,
    forecastWindowType: item.forecastWindowType,
    overallDeliveryStatus: item.overallDeliveryStatus,
    primaryMetricLabel: 'Forecast',
    primaryMetricValue: item.forecastValue,
    secondaryMetricLabel: 'Threshold',
    secondaryMetricValue: item.thresholdValue,
  };
}

function toSurgeAlertSummary(item: SurgeAlertEventSummary): AlertSummary {
  return {
    alertSource: 'surge_alert',
    alertId: item.surgeNotificationEventId,
    sourceLabel: 'Surge',
    serviceCategory: item.serviceCategory,
    createdAt: item.createdAt,
    windowStart: item.evaluationWindowStart,
    windowEnd: item.evaluationWindowEnd,
    forecastWindowType: 'hourly',
    overallDeliveryStatus: item.overallDeliveryStatus,
    primaryMetricLabel: 'Actual',
    primaryMetricValue: item.actualDemandValue,
    secondaryMetricLabel: 'Forecast P50',
    secondaryMetricValue: item.forecastP50Value,
  };
}

function mergeAlertSummaries(thresholdEvents: ThresholdAlertEventSummary[], surgeEvents: SurgeAlertEventSummary[]): AlertSummary[] {
  return [
    ...(thresholdEvents ?? []).map(toThresholdAlertSummary),
    ...(surgeEvents ?? []).map(toSurgeAlertSummary),
  ].sort((left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime());
}

function StatusBadge({ status }: { status: OverallDeliveryStatus }) {
  const state = deliveryStatusStyle(status);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${state.bg} ${state.text}`}>
      <span aria-hidden="true">{state.icon}</span>
      {state.label}
    </span>
  );
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pt-3">
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(25,58,90,0.12)] to-transparent" />
      <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-muted/60">{label}</span>
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(25,58,90,0.12)] to-transparent" />
    </div>
  );
}

function sourceBadgeClasses(sourceLabel: AlertSummary['sourceLabel']): string {
  return sourceLabel === 'Surge'
    ? 'border-amber-200 bg-amber-50 text-amber-800'
    : 'border-sky-200 bg-sky-50 text-sky-800';
}

function ForecastStyleSingleSelect<T extends string>({
  buttonId,
  value,
  options,
  placeholder,
  isOpen,
  onOpenChange,
  onChange,
  containerRef,
  ariaLabel,
  scrollable = false,
}: {
  buttonId: string;
  value: T | '';
  options: Array<{ value: T; label: string }>;
  placeholder: string;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onChange: (value: T) => void;
  containerRef: RefObject<HTMLDivElement>;
  ariaLabel: string;
  scrollable?: boolean;
}) {
  const selectedLabel = options.find((option) => option.value === value)?.label ?? placeholder;

  return (
    <div ref={containerRef} className={isOpen ? 'relative z-[120]' : 'relative z-10'}>
      <button
        id={buttonId}
        type="button"
        onClick={() => onOpenChange(!isOpen)}
        className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
      >
        <span>{selectedLabel}</span>
        <span className="ml-4 text-muted">{isOpen ? 'Hide' : 'Choose'}</span>
      </button>
      {isOpen ? (
        <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
          <div role="listbox" aria-label={ariaLabel} className={scrollable ? 'max-h-64 space-y-2 overflow-auto' : 'space-y-2'}>
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value);
                  onOpenChange(false);
                }}
                className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                aria-pressed={value === option.value}
              >
                <span>{option.label}</span>
                {value === option.value ? <span className="text-forecast">Selected</span> : null}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

type ThresholdFormState = {
  serviceCategory: string;
  forecastWindowType: ForecastWindowType;
  thresholdValue: string;
};

const EMPTY_FORM: ThresholdFormState = {
  serviceCategory: '',
  forecastWindowType: 'hourly',
  thresholdValue: '10',
};

export function AlertReviewPage({ roles }: { roles: string[] }) {
  const [activePanel, setActivePanel] = useState<'alerts' | 'surges'>('alerts');
  const [thresholdEvents, setThresholdEvents] = useState<ThresholdAlertEventSummary[]>([]);
  const [surgeEvents, setSurgeEvents] = useState<SurgeAlertEventSummary[]>([]);
  const [thresholds, setThresholds] = useState<ThresholdConfiguration[]>([]);
  const [serviceCategories, setServiceCategories] = useState<string[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<AlertSummary | null>(null);
  const [editingThresholdId, setEditingThresholdId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formState, setFormState] = useState(EMPTY_FORM);
  const [openDropdown, setOpenDropdown] = useState<'serviceCategory' | 'forecastWindow' | null>(null);
  const serviceCategoryRef = useRef<HTMLDivElement>(null);
  const forecastWindowRef = useRef<HTMLDivElement>(null);
  const readable = canReadAlerts(roles);
  const writable = canWriteThresholds(roles);
  const {
    detail,
    isLoading: isDetailLoading,
    error: detailError,
    reportRenderSuccess,
    reportRenderFailure,
  } = useAlertDetail(selectedAlert);

  useEffect(() => {
    if (!readable) return;
    Promise.all([
      fetchThresholdServiceCategories(),
      fetchThresholdAlertConfigurations(),
      fetchThresholdAlertEvents(),
      fetchSurgeEvents(),
    ])
      .then(([categoryItems, thresholdItems, thresholdEventItems, surgeEventItems]) => {
        setServiceCategories(mergeServiceCategories(categoryItems, thresholdItems, ''));
        setThresholds(thresholdItems);
        setThresholdEvents(thresholdEventItems);
        setSurgeEvents(surgeEventItems);
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : 'Unable to load alerts.');
      });
  }, [readable]);

  useEffect(() => {
    const mergedAlerts = mergeAlertSummaries(thresholdEvents, surgeEvents);
    if (mergedAlerts.length === 0) {
      setSelectedAlert(null);
      return;
    }
    if (!selectedAlert) {
      setSelectedAlert(mergedAlerts[0]);
      return;
    }
    const stillSelected = mergedAlerts.some(
      (item) => item.alertSource === selectedAlert.alertSource && item.alertId === selectedAlert.alertId,
    );
    if (!stillSelected) {
      setSelectedAlert(mergedAlerts[0]);
    }
  }, [selectedAlert, thresholdEvents, surgeEvents]);

  useEffect(() => {
    if (!openDropdown) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (serviceCategoryRef.current?.contains(target) || forecastWindowRef.current?.contains(target)) {
        return;
      }
      setOpenDropdown(null);
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [openDropdown]);

  function updateForm(patch: Partial<ThresholdFormState>): void {
    setFormState((current) => ({ ...current, ...patch }));
  }

  function resetForm(): void {
    setEditingThresholdId(null);
    setFormState(EMPTY_FORM);
    setSaveError(null);
  }

  function populateForm(configuration: ThresholdConfiguration): void {
    setEditingThresholdId(configuration.thresholdConfigurationId);
    setFormState({
      serviceCategory: configuration.serviceCategory,
      forecastWindowType: configuration.forecastWindowType,
      thresholdValue: String(configuration.thresholdValue),
    });
    setSaveError(null);
  }

  async function refreshThresholds(): Promise<void> {
    const thresholdItems = await fetchThresholdAlertConfigurations();
    setThresholds(thresholdItems);
    setServiceCategories((current) => mergeServiceCategories(current, thresholdItems, formState.serviceCategory));
  }

  function refreshAlertSummariesSoon(): void {
    setTimeout(() => {
      void Promise.all([fetchThresholdAlertEvents(), fetchSurgeEvents()]).then(([thresholdItems, surgeItems]) => {
        setThresholdEvents(thresholdItems);
        setSurgeEvents(surgeItems);
      });
    }, 1000);
  }

  async function handleSaveThreshold(): Promise<void> {
    if (!formState.serviceCategory) {
      setSaveError('Select a service category.');
      return;
    }
    const parsedThresholdValue = Number(formState.thresholdValue);
    if (!Number.isFinite(parsedThresholdValue) || !Number.isInteger(parsedThresholdValue) || parsedThresholdValue < 1) {
      setSaveError('Enter a whole-number threshold value of at least 1.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    const payload: ThresholdConfigurationWrite = {
      serviceCategory: formState.serviceCategory,
      forecastWindowType: formState.forecastWindowType,
      thresholdValue: parsedThresholdValue,
      notificationChannels: ['dashboard'],
    };

    try {
      const saved = editingThresholdId
        ? await updateThresholdConfiguration(editingThresholdId, payload)
        : await createThresholdConfiguration(payload);

      setThresholds((current) => {
        const exists = current.some((item) => item.thresholdConfigurationId === saved.thresholdConfigurationId);
        if (exists) {
          return current.map((item) => (item.thresholdConfigurationId === saved.thresholdConfigurationId ? saved : item));
        }
        return [...current, saved];
      });
      await refreshThresholds();
      refreshAlertSummariesSoon();
      resetForm();
    } catch (requestError) {
      setSaveError(requestError instanceof Error ? requestError.message : 'Unable to save threshold.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteThreshold(thresholdConfigurationId: string): Promise<void> {
    setSaveError(null);
    try {
      await deleteThresholdConfiguration(thresholdConfigurationId);
      setThresholds((current) =>
        current.map((item) =>
          item.thresholdConfigurationId === thresholdConfigurationId ? { ...item, status: 'inactive' } : item,
        ),
      );
      if (editingThresholdId === thresholdConfigurationId) {
        resetForm();
      }
    } catch (requestError) {
      setSaveError(requestError instanceof Error ? requestError.message : 'Unable to delete threshold.');
    }
  }

  if (!readable) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
        <Alert variant="destructive">
          <AlertTitle>Alert access is restricted</AlertTitle>
          <AlertDescription>Your current role does not include alert review access.</AlertDescription>
        </Alert>
      </main>
    );
  }

  const mergedAlerts = mergeAlertSummaries(thresholdEvents, surgeEvents);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setActivePanel('alerts')}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
            activePanel === 'alerts' ? 'bg-accent text-white' : 'bg-white text-ink'
          }`}
        >
          Alerts
        </button>
        <button
          type="button"
          onClick={() => setActivePanel('surges')}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
            activePanel === 'surges' ? 'bg-accent text-white' : 'bg-white text-ink'
          }`}
        >
          Surge Evaluations
        </button>
      </div>

      {activePanel === 'surges' ? <SurgeAlertReview roles={roles} /> : null}

      {activePanel === 'alerts' ? (
        <div className="grid items-start gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Card className="rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
            <CardHeader>
              <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Alert Review</p>
              <CardTitle className="text-3xl text-ink">Set thresholds and inspect threshold plus surge alerts</CardTitle>
              <CardDescription>Manage threshold configurations, then drill into a unified list of recorded threshold and surge alerts.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}

              {writable ? (
                <div
                  className="grid gap-3 rounded-2xl border border-[rgba(25,58,90,0.10)] p-4"
                  style={{
                    background: 'linear-gradient(135deg, rgba(241,247,252,0.9) 0%, rgba(255,255,255,0.95) 100%)',
                  }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="m-0 flex items-center gap-2 text-sm font-bold text-ink">
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-lg bg-accent/10 text-xs text-accent">
                        {editingThresholdId ? '✎' : '+'}
                      </span>
                      {editingThresholdId ? 'Edit threshold' : 'Add threshold'}
                    </p>
                    {editingThresholdId ? (
                      <button
                        type="button"
                        onClick={resetForm}
                        className="text-xs font-bold uppercase tracking-wider text-accent transition hover:text-accent-strong"
                      >
                        Cancel
                      </button>
                    ) : null}
                  </div>

                  <label className="grid gap-1.5 text-sm font-medium text-ink">
                    <span>Service category</span>
                    <ForecastStyleSingleSelect
                      buttonId="service-category"
                      value={formState.serviceCategory}
                      options={mergeServiceCategories(serviceCategories, thresholds, formState.serviceCategory).map((item) => ({
                        value: item,
                        label: item,
                      }))}
                      placeholder="Select a category"
                      isOpen={openDropdown === 'serviceCategory'}
                      onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'serviceCategory' : null)}
                      onChange={(value) => updateForm({ serviceCategory: value })}
                      containerRef={serviceCategoryRef}
                      ariaLabel="Service category"
                      scrollable
                    />
                  </label>

                  <label className="grid gap-1.5 text-sm font-medium text-ink">
                    <span>Forecast window</span>
                    <ForecastStyleSingleSelect
                      buttonId="forecast-window"
                      value={formState.forecastWindowType}
                      options={FORECAST_WINDOW_OPTIONS}
                      placeholder="Select a forecast window"
                      isOpen={openDropdown === 'forecastWindow'}
                      onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'forecastWindow' : null)}
                      onChange={(value) => updateForm({ forecastWindowType: value })}
                      containerRef={forecastWindowRef}
                      ariaLabel="Forecast window"
                    />
                  </label>

                  <label className="grid gap-1.5 text-sm font-medium text-ink">
                    <span>Threshold value</span>
                    <Input
                      type="number"
                      min="1"
                      step="1"
                      value={formState.thresholdValue}
                      onChange={(event) => updateForm({ thresholdValue: event.target.value })}
                      placeholder="Threshold value"
                      aria-label="Threshold value"
                    />
                  </label>

                  {saveError ? <p className="text-sm font-medium text-red-700">{saveError}</p> : null}

                  <button
                    type="button"
                    onClick={() => {
                      void handleSaveThreshold();
                    }}
                    disabled={isSaving}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-accent px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-accent-strong hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isSaving ? <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> : null}
                    {editingThresholdId ? 'Update threshold' : 'Save threshold'}
                  </button>
                </div>
              ) : null}

              <SectionDivider label="Active thresholds" />

              <div className="grid max-h-96 gap-3 overflow-auto">
                {thresholds.filter((item) => item.status === 'active').length === 0 ? (
                  <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 py-8 text-center">
                    <span className="text-3xl opacity-30">⊘</span>
                    <p className="text-sm text-muted">No thresholds configured yet.</p>
                  </div>
                ) : null}
                {thresholds.filter((item) => item.status === 'active').map((item) => (
                  <div
                    key={item.thresholdConfigurationId}
                    className="group grid gap-3 rounded-[22px] border border-white/80 px-5 py-4 text-sm text-ink shadow-[0_8px_28px_rgba(15,23,42,0.06)] transition-shadow hover:shadow-[0_14px_38px_rgba(15,23,42,0.10)]"
                    style={{
                      background: 'linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(241,247,252,0.95) 100%)',
                    }}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-0.5">
                        <p className="text-base font-bold leading-tight text-ink">{item.serviceCategory}</p>
                        <p className="text-sm text-muted">
                          Alert at ≥ <span className="font-bold text-ink">{item.thresholdValue}</span> forecasted requests
                        </p>
                      </div>
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-800">
                        <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        active
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/15 bg-accent/5 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-accent">
                        ◷ {item.forecastWindowType}
                      </span>
                    </div>

                    {writable ? (
                      <div className="flex flex-wrap gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => populateForm(item)}
                          className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 text-xs font-bold text-ink shadow-sm transition hover:border-accent hover:shadow-md"
                        >
                          ✎ Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            void handleDeleteThreshold(item.thresholdConfigurationId);
                          }}
                          className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-4 text-xs font-bold text-red-600 transition hover:border-red-300 hover:bg-red-100"
                        >
                          ✕ Delete
                        </button>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>

              <SectionDivider label="Recorded alerts" />

              <div className="grid max-h-96 gap-2 overflow-auto">
                {mergedAlerts.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 py-8 text-center">
                    <span className="text-3xl opacity-30">🔔</span>
                    <p className="text-sm text-muted">No threshold or surge alerts have been recorded yet.</p>
                  </div>
                ) : null}
                {mergedAlerts.map((item) => {
                  const active = selectedAlert?.alertSource === item.alertSource && selectedAlert.alertId === item.alertId;
                  return (
                    <button
                      key={`${item.alertSource}-${item.alertId}`}
                      type="button"
                      onClick={() => setSelectedAlert(item)}
                      className={`group grid gap-2 rounded-2xl border px-4 py-3 text-left transition-all ${
                        active
                          ? 'border-accent/30 bg-accent/[0.04] shadow-[0_4px_16px_rgba(0,80,135,0.10)]'
                          : 'border-slate-200 bg-slate-50/70 hover:border-accent/20 hover:bg-white hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className={`text-sm font-bold ${active ? 'text-accent' : 'text-ink'}`}>{item.serviceCategory}</p>
                            <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${sourceBadgeClasses(item.sourceLabel)}`}>
                              {item.sourceLabel}
                            </span>
                          </div>
                          <p className="text-xs text-muted">
                            <span className="capitalize">{item.forecastWindowType}</span> · {formatDateTime(item.createdAt)}
                          </p>
                        </div>
                        <StatusBadge status={item.overallDeliveryStatus} />
                      </div>
                      <div className="flex flex-wrap gap-3 text-xs text-muted">
                        <span>{item.primaryMetricLabel} <span className="font-semibold text-ink">{item.primaryMetricValue}</span></span>
                        <span>{item.secondaryMetricLabel} <span className="font-semibold text-ink">{item.secondaryMetricValue}</span></span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <div className="lg:sticky lg:top-7 lg:self-start">
            <AlertDetailPanel
              selectedAlert={selectedAlert}
              detail={detail}
              isLoading={isDetailLoading}
              error={detailError}
              onRenderSuccess={reportRenderSuccess}
              onRenderFailure={reportRenderFailure}
            />
          </div>
        </div>
      ) : null}
    </main>
  );
}
