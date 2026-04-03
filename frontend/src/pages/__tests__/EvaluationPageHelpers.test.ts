import { describe, expect, it, vi } from 'vitest';
import {
  canReadEvaluation,
  canTriggerEvaluation,
  describeRunStatus,
  formatDateTime,
  formatUpdatedDateTime,
  wait,
} from '../EvaluationPage';

describe('EvaluationPage helper functions', () => {
  it('formats missing dates as Not available', () => {
    expect(formatDateTime(undefined)).toBe('Not available');
    expect(formatDateTime(null)).toBe('Not available');
    expect(formatUpdatedDateTime(undefined)).toBe('Not available');
    expect(formatUpdatedDateTime(null)).toBe('Not available');
  });

  it('formats updated dates without minutes or seconds', () => {
    const formatted = formatUpdatedDateTime('2026-03-25T10:05:00Z');
    expect(formatted).toContain('2026');
    expect(formatted).not.toContain(':05');
  });

  it('checks role-based access and trigger permissions', () => {
    expect(canReadEvaluation(['CityPlanner'])).toBe(true);
    expect(canReadEvaluation(['OperationalManager'])).toBe(true);
    expect(canReadEvaluation(['Viewer'])).toBe(false);

    expect(canTriggerEvaluation(['OperationalManager'])).toBe(true);
    expect(canTriggerEvaluation(['CityPlanner'])).toBe(false);
  });

  it('describes run status across all branches', () => {
    expect(describeRunStatus(null)).toBe('No run started in this session.');
    expect(describeRunStatus({ status: 'running' } as any)).toBe('Evaluation is running.');

    expect(
      describeRunStatus({ status: 'failed', failureReason: 'Timed out', summary: null } as any),
    ).toBe('Timed out');
    expect(
      describeRunStatus({ status: 'failed', failureReason: null, summary: 'Backend error summary' } as any),
    ).toBe('Backend error summary');
    expect(
      describeRunStatus({ status: 'failed', failureReason: null, summary: null } as any),
    ).toBe('Evaluation failed.');

    expect(describeRunStatus({ status: 'success', summary: 'Completed successfully' } as any)).toBe(
      'Completed successfully',
    );
    expect(describeRunStatus({ status: 'success', summary: null } as any)).toBe(
      'Evaluation completed.',
    );
  });

  it('wait resolves after the timer duration', async () => {
    vi.useFakeTimers();
    const waiter = wait(5);
    await vi.advanceTimersByTimeAsync(5);
    await expect(waiter).resolves.toBeUndefined();
    vi.useRealTimers();
  });
});
