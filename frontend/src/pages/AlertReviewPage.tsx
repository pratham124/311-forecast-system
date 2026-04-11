import { useEffect, useRef, useState, type RefObject } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { SurgeAlertReview } from '../features/surge_alerts';
import {
  createThresholdConfiguration,
  deleteThresholdConfiguration,
  fetchThresholdAlertConfigurations,
  fetchThresholdAlertEvent,
  fetchThresholdAlertEvents,
  fetchThresholdServiceCategories,
  updateThresholdConfiguration,
} from '../api/forecastAlerts';
import type {
  ForecastWindowType,
  ThresholdAlertEvent,
  ThresholdAlertEventSummary,
  ThresholdConfiguration,
  ThresholdConfigurationWrite,
  OverallDeliveryStatus,
} from '../types/forecastAlerts';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);
const WRITER_ROLES = new Set(['OperationalManager']);
const FORECAST_WINDOW_OPTIONS: Array<{ value: ForecastWindowType; label: string }> = [
  { value: 'hourly', label: 'Hourly' },
  { value: 'daily', label: 'Daily' },
];


/* ── Status styling helpers ────────────────────────────────────────── */

const STATUS_STYLES: Record<OverallDeliveryStatus, { bg: string; text: string; icon: string; label: string }> = {
  delivered: { bg: 'bg-emerald-50', text: 'text-emerald-700', icon: '✓', label: 'Delivered' },
  partial_delivery: { bg: 'bg-amber-50', text: 'text-amber-700', icon: '◐', label: 'Partial' },
  retry_pending: { bg: 'bg-sky-50', text: 'text-sky-700', icon: '↻', label: 'Retry Pending' },
  manual_review_required: { bg: 'bg-red-50', text: 'text-red-700', icon: '!', label: 'Review Required' },
};

function deliveryStatusStyle(status: OverallDeliveryStatus) {
  return STATUS_STYLES[status] ?? STATUS_STYLES.delivered;
}



/* ── Shared utility functions ──────────────────────────────────────── */

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

/* ── Small shared components ───────────────────────────────────────── */

function StatusBadge({ status }: { status: OverallDeliveryStatus }) {
  const s = deliveryStatusStyle(status);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${s.bg} ${s.text}`}>
      <span aria-hidden="true">{s.icon}</span>
      {s.label}
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

function ForecastGauge({ forecast, threshold }: { forecast: number; threshold: number }) {
  const max = Math.max(forecast, threshold) * 1.3;
  const forecastPct = Math.min((forecast / max) * 100, 100);
  const thresholdPct = Math.min((threshold / max) * 100, 100);
  const exceeded = forecast >= threshold;

  return (
    <div className="grid gap-2">
      <div className="flex items-baseline justify-between text-xs font-semibold">
        <span className="text-muted">Forecast vs Threshold</span>
        <span className={exceeded ? 'text-red-600' : 'text-emerald-600'}>
          {exceeded ? 'Exceeded' : 'Within limit'}
        </span>
      </div>
      <div className="relative h-5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${forecastPct}%`,
            background: exceeded
              ? 'linear-gradient(90deg, #f87171, #dc2626)'
              : 'linear-gradient(90deg, #34d399, #059669)',
          }}
        />
        <div
          className="absolute inset-y-0 w-0.5 bg-ink/40"
          style={{ left: `${thresholdPct}%` }}
          title={`Threshold: ${threshold}`}
        />
      </div>
      <div className="flex justify-between text-xs text-muted">
        <span>Forecast: <span className="font-semibold text-ink">{forecast}</span></span>
        <span>Threshold: <span className="font-semibold text-ink">{threshold}</span></span>
      </div>
    </div>
  );
}

function formatChannelType(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function attemptStatusClasses(status: 'succeeded' | 'failed'): string {
  return status === 'succeeded'
    ? 'border-emerald-200 bg-emerald-50/80 text-emerald-800'
    : 'border-red-200 bg-red-50/80 text-red-800';
}

/* ── Dropdown sub-component ────────────────────────────────────────── */

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



/* ── Form state ────────────────────────────────────────────────────── */

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

/* ── Main page component ───────────────────────────────────────────── */

export function AlertReviewPage({ roles }: { roles: string[] }) {
  const [activePanel, setActivePanel] = useState<'thresholds' | 'surges'>('thresholds');
  const [events, setEvents] = useState<ThresholdAlertEventSummary[]>([]);
  const [thresholds, setThresholds] = useState<ThresholdConfiguration[]>([]);
  const [serviceCategories, setServiceCategories] = useState<string[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<ThresholdAlertEvent | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
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

  useEffect(() => {
    if (!readable) return;
    Promise.all([fetchThresholdServiceCategories(), fetchThresholdAlertConfigurations(), fetchThresholdAlertEvents()])
      .then(async ([categoryItems, thresholdItems, eventItems]) => {
        setServiceCategories(mergeServiceCategories(categoryItems, thresholdItems, ''));
        setThresholds(thresholdItems);
        setEvents(eventItems);
        if (eventItems[0]) {
          setSelectedEventId(eventItems[0].notificationEventId);
          setSelectedEvent(await fetchThresholdAlertEvent(eventItems[0].notificationEventId));
        }
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : 'Unable to load alerts.');
      });
  }, [readable]);

  useEffect(() => {
    if (!openDropdown) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (
        serviceCategoryRef.current?.contains(target)
        || forecastWindowRef.current?.contains(target)
      ) {
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
      let saved: ThresholdConfiguration;
      if (editingThresholdId) {
        saved = await updateThresholdConfiguration(editingThresholdId, payload);
      } else {
        saved = await createThresholdConfiguration(payload);
      }

      // Immediately update local state so the UI reflects the change
      setThresholds((current) => {
        const exists = current.some((t) => t.thresholdConfigurationId === saved.thresholdConfigurationId);
        if (exists) {
          return current.map((t) => (t.thresholdConfigurationId === saved.thresholdConfigurationId ? saved : t));
        }
        return [...current, saved];
      });
      setServiceCategories((current) => mergeServiceCategories(current, thresholds, saved.serviceCategory));
      
      // The background task evaluates alerts immediately after saving. 
      // Give it a brief delay to finish, then fetch the latest events so new ones appear!
      setTimeout(() => {
        void fetchThresholdAlertEvents().then(setEvents);
      }, 1000);

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
      // Immediately remove from local state
      setThresholds((current) =>
        current.map((t) =>
          t.thresholdConfigurationId === thresholdConfigurationId ? { ...t, status: 'inactive' } : t,
        ),
      );
      if (editingThresholdId === thresholdConfigurationId) {
        resetForm();
      }
    } catch (requestError) {
      setSaveError(requestError instanceof Error ? requestError.message : 'Unable to delete threshold.');
    }
  }

  function handleSelectEvent(eventId: string): void {
    setSelectedEventId(eventId);
    void fetchThresholdAlertEvent(eventId).then(setSelectedEvent);
  }

  if (!readable) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
        <Alert variant="destructive">
          <AlertTitle>Alert access is restricted</AlertTitle>
          <AlertDescription>Your current role does not include threshold alert review access.</AlertDescription>
        </Alert>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setActivePanel('thresholds')}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
            activePanel === 'thresholds' ? 'bg-accent text-white' : 'bg-white text-ink'
          }`}
        >
          Threshold Alerts
        </button>
        <button
          type="button"
          onClick={() => setActivePanel('surges')}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
            activePanel === 'surges' ? 'bg-accent text-white' : 'bg-white text-ink'
          }`}
        >
          Surge Alerts
        </button>
      </div>

      {activePanel === 'surges' ? <SurgeAlertReview roles={roles} /> : null}
      {activePanel === 'thresholds' ? (
        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      {/* ─── Left column: Thresholds & event list ──────────────── */}
      <Card className="rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
        <CardHeader>
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Threshold Alerts</p>
          <CardTitle className="text-3xl text-ink">Set thresholds and review alert outcomes</CardTitle>
          <CardDescription>Create category thresholds and inspect delivered, partial-delivery, and failed alerts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}

          {/* ── Threshold form ─────────────────────────────────── */}
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
                {isSaving ? (
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                ) : null}
                {editingThresholdId ? 'Update threshold' : 'Save threshold'}
              </button>
            </div>
          ) : null}

          {/* ── Current thresholds ─────────────────────────────── */}
          <SectionDivider label="Active thresholds" />

          <div className="grid max-h-96 gap-3 overflow-auto">
            {thresholds.filter((t) => t.status === 'active').length === 0 ? (
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
                      disabled={false}
                      className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-4 text-xs font-bold text-red-600 transition hover:border-red-300 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      ✕ Delete
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>

          {/* ── Recorded alerts list ──────────────────────────── */}
          <SectionDivider label="Recorded alerts" />

          <div className="grid max-h-96 gap-2 overflow-auto">
            {events.length === 0 ? (
              <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 py-8 text-center">
                <span className="text-3xl opacity-30">🔔</span>
                <p className="text-sm text-muted">No alert events recorded yet.</p>
              </div>
            ) : null}
            {events.map((item) => {
              const active = selectedEventId === item.notificationEventId;
              const s = deliveryStatusStyle(item.overallDeliveryStatus);
              return (
                <button
                  key={item.notificationEventId}
                  type="button"
                  onClick={() => handleSelectEvent(item.notificationEventId)}
                  className={`group grid gap-1.5 rounded-2xl border px-4 py-3 text-left transition-all ${
                    active
                      ? 'border-accent/30 bg-accent/[0.04] shadow-[0_4px_16px_rgba(0,80,135,0.10)]'
                      : 'border-slate-200 bg-slate-50/70 hover:border-accent/20 hover:bg-white hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-sm font-bold ${active ? 'text-accent' : 'text-ink'}`}>{item.serviceCategory}</p>
                    <StatusBadge status={item.overallDeliveryStatus} />
                  </div>
                  <p className="text-xs text-muted">
                    <span className="capitalize">{item.forecastWindowType}</span> · {formatDateTime(item.createdAt)}
                  </p>
                  <div className="mt-1 flex items-center gap-3 text-xs text-muted">
                    <span>Forecast <span className="font-semibold text-ink">{item.forecastValue}</span></span>
                    <span className="text-slate-300">|</span>
                    <span>Threshold <span className="font-semibold text-ink">{item.thresholdValue}</span></span>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ─── Right column: Alert detail ────────────────────────── */}
      <div className="lg:sticky lg:top-7 lg:self-start">
        <Card className="overflow-hidden rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
          {/* Decorative gradient bar */}
          <div
            className="h-1.5"
            style={{
              background: selectedEvent
                ? selectedEvent.forecastValue >= selectedEvent.thresholdValue
                  ? 'linear-gradient(90deg, #f87171, #dc2626, #b91c1c)'
                  : 'linear-gradient(90deg, #34d399, #059669, #047857)'
                : 'linear-gradient(90deg, #005087, #0081BC, #38bdf8)',
            }}
          />
          <CardHeader>
            <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Alert Inspector</p>
            <CardTitle className="text-2xl text-ink">Alert Detail</CardTitle>
            <CardDescription>Inspect scope, forecast values, and threshold outcomes.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            {selectedEvent ? (
              <>
                {/* Category & status header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-lg font-bold text-ink">{selectedEvent.serviceCategory}</p>
                    <p className="text-xs text-muted">
                      <span className="capitalize">{selectedEvent.forecastWindowType}</span> window from{' '}
                      {formatDateTime(selectedEvent.forecastWindowStart)}
                    </p>
                  </div>
                  <StatusBadge status={selectedEvent.overallDeliveryStatus} />
                </div>

                {/* Forecast gauge */}
                <ForecastGauge forecast={selectedEvent.forecastValue} threshold={selectedEvent.thresholdValue} />

                {/* Key-value grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-muted/70">Forecast</p>
                    <p className="mt-1 text-xl font-bold text-ink">{selectedEvent.forecastValue}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-muted/70">Threshold</p>
                    <p className="mt-1 text-xl font-bold text-ink">{selectedEvent.thresholdValue}</p>
                  </div>
                </div>

                {selectedEvent.followUpReason ? (
                  <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-4 py-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700/70">Follow-up Reason</p>
                    <p className="mt-1 text-sm font-medium text-amber-900">{selectedEvent.followUpReason}</p>
                  </div>
                ) : null}




              </>
            ) : (
              <div className="flex flex-col items-center gap-3 py-10 text-center">
                <span className="text-5xl opacity-20">📋</span>
                <p className="text-sm font-medium text-muted">Select an alert from the list to inspect its details.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
        </div>
      ) : null}
    </main>
  );
}
