import { describe, expect, it, vi } from 'vitest';
import {
  canReadIngestion,
  canTriggerIngestion,
  describeRunStatus,
  formatDateTime,
  formatUpdatedDateTime,
  wait,
} from '../IngestionPage';

describe('IngestionPage helper functions', () => {
  it('formats missing date values as Not available', () => {
    expect(formatDateTime(undefined)).toBe('Not available');
    expect(formatDateTime(null)).toBe('Not available');
    expect(formatUpdatedDateTime(undefined)).toBe('Not available');
    expect(formatUpdatedDateTime(null)).toBe('Not available');
  });

  it('formats compact date values without minutes or seconds', () => {
    const formatted = formatUpdatedDateTime('2026-03-25T10:05:00Z');
    expect(formatted).toContain('2026');
    expect(formatted).not.toContain(':05');
  });

  it('checks role-based read and trigger permissions', () => {
    expect(canReadIngestion(['CityPlanner'])).toBe(true);
    expect(canReadIngestion(['OperationalManager'])).toBe(true);
    expect(canReadIngestion(['Viewer'])).toBe(false);

    expect(canTriggerIngestion(['OperationalManager'])).toBe(true);
    expect(canTriggerIngestion(['CityPlanner'])).toBe(false);
  });

  it('describes run status across all branches', () => {
    expect(describeRunStatus(null)).toBe('No run started in this session.');
    expect(describeRunStatus({ status: 'running' } as any)).toBe('311 ingestion is running.');
    expect(describeRunStatus({ status: 'failed', failureReason: 'bad source' } as any)).toBe('bad source');
    expect(describeRunStatus({ status: 'failed', failureReason: null } as any)).toBe('311 ingestion failed.');
    expect(describeRunStatus({ status: 'success' } as any)).toBe('311 ingestion completed.');
  });

  it('wait resolves after timers advance', async () => {
    vi.useFakeTimers();
    const waiter = wait(5);
    await vi.advanceTimersByTimeAsync(5);
    await expect(waiter).resolves.toBeUndefined();
    vi.useRealTimers();
  });
});
