import { useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
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
} from '../types/forecastAlerts';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);
const WRITER_ROLES = new Set(['OperationalManager']);
const FORECAST_WINDOW_OPTIONS: Array<{ value: ForecastWindowType; label: string }> = [
  { value: 'hourly', label: 'Hourly' },
  { value: 'daily', label: 'Daily' },
];
const CHANNEL_PRESET_OPTIONS = [
  { value: 'email', label: 'Email', channels: ['email'] },
  { value: 'dashboard', label: 'Dashboard', channels: ['dashboard'] },
  { value: 'sms', label: 'SMS', channels: ['sms'] },
  { value: 'dashboard,email', label: 'Email + dashboard', channels: ['email', 'dashboard'] },
  { value: 'email,sms', label: 'Email + SMS', channels: ['email', 'sms'] },
  { value: 'dashboard,sms', label: 'Dashboard + SMS', channels: ['dashboard', 'sms'] },
  { value: 'dashboard,email,sms', label: 'Email + dashboard + SMS', channels: ['email', 'dashboard', 'sms'] },
] as const;

const DEFAULT_CHANNEL_PRESET = 'dashboard,email';

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

function normalizeChannelPreset(channels: string[]): string {
  const value = [...channels].sort().join(',');
  const match = CHANNEL_PRESET_OPTIONS.find((option) => option.value === value);
  return match?.value ?? DEFAULT_CHANNEL_PRESET;
}

function formatChannelSelection(channels: string[]): string {
  const value = normalizeChannelPreset(channels);
  return CHANNEL_PRESET_OPTIONS.find((option) => option.value === value)?.label ?? 'Choose channels';
}

function mergeServiceCategories(serviceCategories: string[], thresholds: ThresholdConfiguration[], selectedCategory: string): string[] {
  return [...new Set([...serviceCategories, ...thresholds.map((item) => item.serviceCategory), selectedCategory].filter(Boolean))].sort();
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
  const selectedLabel = useMemo(() => options.find((option) => option.value === value)?.label ?? placeholder, [options, placeholder, value]);

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

function NotificationChannelMultiSelect({
  selectedValues,
  onChange,
  isOpen,
  onOpenChange,
  containerRef,
}: {
  selectedValues: string[];
  onChange: (values: string[]) => void;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  containerRef: RefObject<HTMLDivElement>;
}) {
  const buttonLabel = useMemo(() => {
    if (selectedValues.length === 0) return 'Choose channels';
    return formatChannelSelection(selectedValues);
  }, [selectedValues]);

  const toggleValue = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((item) => item !== value));
      return;
    }
    onChange([...selectedValues, value].sort());
  };

  return (
    <div ref={containerRef} className={isOpen ? 'relative z-[120]' : 'relative z-10'}>
      <button
        id="notification-channels"
        type="button"
        onClick={() => onOpenChange(!isOpen)}
        className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Notification channels"
      >
        <span>{buttonLabel}</span>
        <span className="ml-4 text-muted">{isOpen ? 'Hide' : 'Choose'}</span>
      </button>
      {isOpen ? (
        <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
          <div className="mb-2 flex items-center justify-between">
            <p className="m-0 text-sm font-semibold text-ink">Notification channels</p>
            <button
              type="button"
              onClick={() => onChange([])}
              className="text-sm font-medium text-forecast hover:underline"
            >
              Clear all
            </button>
          </div>
          <div role="listbox" aria-label="Notification channels" className="space-y-2">
            {CHANNEL_PRESET_OPTIONS.slice(0, 3).map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => toggleValue(option.value)}
                className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                aria-pressed={selectedValues.includes(option.value)}
              >
                <span>{option.label}</span>
                {selectedValues.includes(option.value) ? <span className="text-forecast">Selected</span> : null}
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
  notificationChannels: string[];
};

const EMPTY_FORM: ThresholdFormState = {
  serviceCategory: '',
  forecastWindowType: 'hourly',
  thresholdValue: '10',
  notificationChannels: ['dashboard', 'email'],
};

export function AlertReviewPage({ roles }: { roles: string[] }) {
  const [events, setEvents] = useState<ThresholdAlertEventSummary[]>([]);
  const [thresholds, setThresholds] = useState<ThresholdConfiguration[]>([]);
  const [serviceCategories, setServiceCategories] = useState<string[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<ThresholdAlertEvent | null>(null);
  const [editingThresholdId, setEditingThresholdId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formState, setFormState] = useState(EMPTY_FORM);
  const [openDropdown, setOpenDropdown] = useState<'serviceCategory' | 'forecastWindow' | 'notificationChannels' | null>(null);
  const serviceCategoryRef = useRef<HTMLDivElement>(null);
  const forecastWindowRef = useRef<HTMLDivElement>(null);
  const notificationChannelsRef = useRef<HTMLDivElement>(null);
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
        || notificationChannelsRef.current?.contains(target)
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
      notificationChannels: [...configuration.notificationChannels].sort(),
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
    if (formState.notificationChannels.length === 0) {
      setSaveError('Select at least one notification channel.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    const payload: ThresholdConfigurationWrite = {
      serviceCategory: formState.serviceCategory,
      forecastWindowType: formState.forecastWindowType,
      thresholdValue: parsedThresholdValue,
      notificationChannels: [...formState.notificationChannels].sort(),
    };

    try {
      if (editingThresholdId) {
        await updateThresholdConfiguration(editingThresholdId, payload);
      } else {
        await createThresholdConfiguration(payload);
      }
      await refreshThresholds();
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
      await refreshThresholds();
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
          <AlertDescription>Your current role does not include threshold alert review access.</AlertDescription>
        </Alert>
      </main>
    );
  }

  return (
    <main className="mx-auto grid w-full max-w-6xl gap-5 px-4 pb-14 pt-7 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
      <Card className="rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
        <CardHeader>
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Threshold Alerts</p>
          <CardTitle className="text-3xl text-ink">Set thresholds and review alert outcomes</CardTitle>
          <CardDescription>Create category thresholds and inspect delivered, partial-delivery, and failed alerts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}
          {writable ? (
            <div className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-ink">{editingThresholdId ? 'Edit threshold' : 'Add threshold'}</p>
                {editingThresholdId ? (
                  <button
                    type="button"
                    onClick={resetForm}
                    className="text-sm font-semibold text-accent transition hover:text-accent-strong"
                  >
                    Cancel
                  </button>
                ) : null}
              </div>

              <label className="grid gap-1 text-sm font-medium text-ink">
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

              <label className="grid gap-1 text-sm font-medium text-ink">
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

              <label className="grid gap-1 text-sm font-medium text-ink">
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

              <label className="grid gap-1 text-sm font-medium text-ink">
                <span>Notification channels</span>
                <NotificationChannelMultiSelect
                  selectedValues={formState.notificationChannels}
                  onChange={(values) => updateForm({ notificationChannels: values })}
                  isOpen={openDropdown === 'notificationChannels'}
                  onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'notificationChannels' : null)}
                  containerRef={notificationChannelsRef}
                />
              </label>

              {saveError ? <p className="text-sm font-medium text-red-700">{saveError}</p> : null}

              <button
                type="button"
                onClick={() => {
                  void handleSaveThreshold();
                }}
                disabled={isSaving}
                className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
              >
                {editingThresholdId ? 'Update threshold' : 'Save threshold'}
              </button>
            </div>
          ) : null}

          <div className="grid gap-2">
            <p className="text-sm font-semibold text-ink">Current thresholds</p>
            {thresholds.map((item) => (
              <div
                key={item.thresholdConfigurationId}
                className="grid gap-4 rounded-[24px] border border-white/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.98),rgba(241,247,252,0.95))] px-4 py-4 text-sm text-ink shadow-[0_14px_34px_rgba(15,23,42,0.06)]"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-base font-semibold leading-tight text-ink">{item.serviceCategory}</p>
                    <p className="text-sm text-muted">
                      Alert when forecasted demand reaches at least <span className="font-semibold text-ink">{item.thresholdValue}</span>
                    </p>
                  </div>
                  <span
                    className={`inline-flex min-h-9 items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] ${
                      item.status === 'active'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-200 text-slate-600'
                    }`}
                  >
                    {item.status}
                  </span>
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex min-h-9 items-center rounded-full border border-[rgba(25,58,90,0.12)] bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-accent">
                    {item.forecastWindowType}
                  </span>
                  {item.notificationChannels.map((channel) => (
                    <span
                      key={`${item.thresholdConfigurationId}-${channel}`}
                      className="inline-flex min-h-9 items-center rounded-full border border-[rgba(25,58,90,0.12)] bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-ink"
                    >
                      {channel}
                    </span>
                  ))}
                </div>

                {writable ? (
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => populateForm(item)}
                      className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void handleDeleteThreshold(item.thresholdConfigurationId);
                      }}
                      disabled={item.status !== 'active'}
                      className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-4 text-sm font-semibold text-red-700 transition hover:border-red-300 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>

          <p className="pt-2 text-sm font-semibold text-ink">Recorded alerts</p>
          {events.map((item) => (
            <button
              key={item.notificationEventId}
              type="button"
              onClick={() => {
                void fetchThresholdAlertEvent(item.notificationEventId).then(setSelectedEvent);
              }}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-accent"
            >
              <p className="text-sm font-semibold text-ink">{item.serviceCategory}</p>
              <p className="text-sm text-muted">{item.overallDeliveryStatus.replace(/_/g, ' ')} · {formatDateTime(item.createdAt)}</p>
            </button>
          ))}
        </CardContent>
      </Card>

      <Card className="rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
        <CardHeader>
          <CardTitle className="text-2xl text-ink">Alert Detail</CardTitle>
          <CardDescription>Open an alert to inspect scope, values, and per-channel delivery details.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {selectedEvent ? (
            <>
              <div className="grid gap-1 text-sm text-ink">
                <p><strong>Category:</strong> {selectedEvent.serviceCategory}</p>
                <p><strong>Window:</strong> {selectedEvent.forecastWindowType} from {formatDateTime(selectedEvent.forecastWindowStart)}</p>
                <p><strong>Forecast:</strong> {selectedEvent.forecastValue}</p>
                <p><strong>Threshold:</strong> {selectedEvent.thresholdValue}</p>
                <p><strong>Status:</strong> {selectedEvent.overallDeliveryStatus.replace(/_/g, ' ')}</p>
                {selectedEvent.followUpReason ? <p><strong>Follow-up:</strong> {selectedEvent.followUpReason}</p> : null}
              </div>
              <div className="grid gap-2">
                <p className="text-sm font-semibold text-ink">Channel Attempts</p>
                {selectedEvent.channelAttempts.map((attempt) => (
                  <div key={`${attempt.channelType}-${attempt.attemptNumber}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-ink">
                    {attempt.channelType} · {attempt.status}
                    {attempt.failureReason ? ` · ${attempt.failureReason}` : ''}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-muted">Select an alert from the list to inspect its delivery trace.</p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
