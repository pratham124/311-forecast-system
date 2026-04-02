import { describe, expect, it } from 'vitest';
import type {
  DatePreset,
  DemandComparisonAvailability,
  DemandComparisonFilters,
} from '../../../types/demandComparisons';
import {
  applyAvailabilityRules,
  buildDefaultAutoSelection,
  clampIso,
  getDateWindow,
  intersectValues,
  isLikelyNetworkTransportError,
  parseIso,
  pickPreferredPreset,
  resolveAvailableGeographyLevels,
  resolveAvailableGeographyValues,
  toDisplayError,
  uniqueStrings,
  validateDateRange,
} from '../hooks/useDemandComparisons';

const availability: DemandComparisonAvailability = {
  serviceCategories: ['Roads', 'Waste'],
  byCategoryGeography: {
    Roads: {
      geographyLevels: ['ward', 'district'],
      geographyOptions: {
        ward: ['Ward 1', 'Ward 2'],
        district: ['North'],
      },
    },
    Waste: {
      geographyLevels: ['ward'],
      geographyOptions: {
        ward: ['Ward 1'],
      },
    },
  },
  dateConstraints: {
    historicalMin: '2026-03-01T00:00:00Z',
    historicalMax: '2026-03-10T00:00:00Z',
    forecastMin: '2026-03-02T00:00:00Z',
    forecastMax: '2026-03-05T00:00:00Z',
  },
  presets: [
    {
      label: 'Active forecast window',
      timeRangeStart: '2026-03-02T00:00:00Z',
      timeRangeEnd: '2026-03-05T00:00:00Z',
    },
    {
      label: 'Overlap window',
      timeRangeStart: '2026-03-02T00:00:00Z',
      timeRangeEnd: '2026-03-05T00:00:00Z',
    },
  ],
  forecastProduct: 'daily_1_day',
};

const baseFilters: DemandComparisonFilters = {
  serviceCategories: ['Roads'],
  geographyLevel: 'ward',
  geographyValues: ['Ward 1'],
  timeRangeStart: '2026-03-02T00:00:00Z',
  timeRangeEnd: '2026-03-03T00:00:00Z',
};

describe('useDemandComparisons helpers', () => {
  it('detects likely network transport errors', () => {
    expect(isLikelyNetworkTransportError('Load failed')).toBe(true);
    expect(isLikelyNetworkTransportError('failed to fetch')).toBe(true);
    expect(isLikelyNetworkTransportError('NetworkError when attempting to fetch resource.')).toBe(true);
    expect(isLikelyNetworkTransportError('Request failed with status 500')).toBe(false);
  });

  it('maps display errors for network, generic, and non-error values', () => {
    expect(toDisplayError(new Error('  '), 'generic', 'network')).toBe('generic');
    expect(toDisplayError(new Error('failed to fetch'), 'generic', 'network')).toBe('network');
    expect(toDisplayError(new Error('boom'), 'generic', 'network')).toBe('boom');
    expect(toDisplayError('not an error', 'generic', 'network')).toBe('generic');
  });

  it('deduplicates unique non-empty strings', () => {
    expect(uniqueStrings(['Roads', ' Roads ', 'Waste', '', '  '])).toEqual(['Roads', ' Roads ', 'Waste']);
  });

  it('parses and clamps ISO dates across invalid, min, max, and in-range values', () => {
    expect(parseIso(undefined)).toBeNull();
    expect(parseIso('not-a-date')).toBeNull();
    expect(parseIso('2026-03-01T00:00:00Z')).not.toBeNull();

    expect(clampIso('not-a-date', '2026-03-01T00:00:00Z', '2026-03-10T00:00:00Z')).toBe('not-a-date');
    expect(clampIso('2026-02-25T00:00:00Z', '2026-03-01T00:00:00Z', '2026-03-10T00:00:00Z')).toBe('2026-03-01T00:00:00.000Z');
    expect(clampIso('2026-03-25T00:00:00Z', '2026-03-01T00:00:00Z', '2026-03-10T00:00:00Z')).toBe('2026-03-10T00:00:00.000Z');
    expect(clampIso('2026-03-05T12:00:00Z', '2026-03-01T00:00:00Z', '2026-03-10T00:00:00Z')).toBe('2026-03-05T12:00:00.000Z');
  });

  it('intersects value groups and handles empty groups', () => {
    expect(intersectValues([])).toEqual([]);
    expect(intersectValues([['Ward 1', 'Ward 1', 'Ward 2'], ['Ward 1', 'Ward 3']])).toEqual(['Ward 1']);
  });

  it('resolves geography levels and values from category intersections', () => {
    expect(resolveAvailableGeographyLevels(availability, [])).toEqual([]);
    expect(resolveAvailableGeographyLevels(availability, ['Roads', 'Waste'])).toEqual(['ward']);

    const missingByCategory = {
      ...availability,
      byCategoryGeography: undefined,
    } as unknown as DemandComparisonAvailability;
    expect(resolveAvailableGeographyLevels(missingByCategory, ['Roads'])).toEqual([]);

    expect(resolveAvailableGeographyValues(availability, ['Roads', 'Waste'], undefined)).toEqual([]);
    expect(resolveAvailableGeographyValues(availability, ['Roads', 'Waste'], 'ward')).toEqual(['Ward 1']);
    expect(resolveAvailableGeographyValues(missingByCategory, ['Roads'], 'ward')).toEqual([]);

    const missingOptions = {
      ...availability,
      byCategoryGeography: {
        Roads: { geographyLevels: ['ward'], geographyOptions: {} },
        Waste: { geographyLevels: ['ward'], geographyOptions: { ward: ['Ward 1'] } },
      },
    } as DemandComparisonAvailability;
    expect(resolveAvailableGeographyValues(missingOptions, ['Roads'], 'ward')).toEqual([]);
  });

  it('derives date windows from constraints including null and missing constraints', () => {
    expect(getDateWindow(null)).toEqual({});

    const missingConstraints = {
      ...availability,
      dateConstraints: undefined,
    } as unknown as DemandComparisonAvailability;
    expect(getDateWindow(missingConstraints)).toEqual({ start: undefined, end: undefined });

    expect(getDateWindow(availability)).toEqual({
      start: '2026-03-01T00:00:00Z',
      end: '2026-03-10T00:00:00Z',
    });

    const forecastExtendsFurther = {
      ...availability,
      dateConstraints: {
        historicalMin: '2026-03-02T00:00:00Z',
        historicalMax: '2026-03-03T00:00:00Z',
        forecastMin: '2026-03-01T00:00:00Z',
        forecastMax: '2026-03-12T00:00:00Z',
      },
    };
    expect(getDateWindow(forecastExtendsFurther)).toEqual({
      start: '2026-03-01T00:00:00Z',
      end: '2026-03-12T00:00:00Z',
    });
  });

  it('validates range errors for invalid dates, inverted ranges, and bounds', () => {
    const window = { start: '2026-03-01T00:00:00Z', end: '2026-03-10T00:00:00Z' };

    expect(validateDateRange({ ...baseFilters, timeRangeStart: 'bad' }, window)).toBe('Select a valid start and end date.');
    expect(validateDateRange({ ...baseFilters, timeRangeStart: '2026-03-05T00:00:00Z', timeRangeEnd: '2026-03-04T00:00:00Z' }, window)).toBe('End date must be on or after the start date.');
    expect(validateDateRange({ ...baseFilters, timeRangeStart: '2026-02-28T00:00:00Z', timeRangeEnd: '2026-03-04T00:00:00Z' }, window)).toBe('Start date is outside the available comparison window.');
    expect(validateDateRange({ ...baseFilters, timeRangeStart: '2026-03-04T00:00:00Z', timeRangeEnd: '2026-03-11T00:00:00Z' }, window)).toBe('End date is outside the available comparison window.');
    expect(validateDateRange(baseFilters, window)).toBeNull();
  });

  it('applies availability rules by sanitizing categories/geographies and normalizing inverted clamped ranges', () => {
    const next = applyAvailabilityRules(
      {
        serviceCategories: ['Roads', 'Unknown'],
        geographyLevel: 'neighbourhood',
        geographyValues: ['North'],
        timeRangeStart: '2026-03-11T00:00:00Z',
        timeRangeEnd: '2026-02-25T00:00:00Z',
      },
      availability,
      { start: '2026-03-01T00:00:00Z', end: '2026-03-10T00:00:00Z' },
    );

    expect(next.serviceCategories).toEqual(['Roads']);
    expect(next.geographyLevel).toBeUndefined();
    expect(next.geographyValues).toEqual([]);
    expect(next.timeRangeStart).toBe('2026-03-10T00:00:00.000Z');
    expect(next.timeRangeEnd).toBe('2026-03-10T00:00:00.000Z');
  });

  it('picks overlap presets first and falls back to first preset', () => {
    const overlap = pickPreferredPreset(availability.presets);
    expect(overlap?.label).toBe('Overlap window');

    const noOverlap: DatePreset[] = [
      { label: 'Active window', timeRangeStart: '2026-03-01T00:00:00Z', timeRangeEnd: '2026-03-02T00:00:00Z' },
      { label: 'Recent', timeRangeStart: '2026-03-03T00:00:00Z', timeRangeEnd: '2026-03-04T00:00:00Z' },
    ];
    expect(pickPreferredPreset(noOverlap)?.label).toBe('Active window');
  });

  it('builds default auto-selection from presets or falls back when no category exists', () => {
    expect(
      buildDefaultAutoSelection(
        { ...availability, serviceCategories: [] },
        { start: '2026-03-01T00:00:00Z', end: '2026-03-10T00:00:00Z' },
        baseFilters,
      ),
    ).toBeNull();

    const selected = buildDefaultAutoSelection(
      availability,
      { start: '2026-03-01T00:00:00Z', end: '2026-03-10T00:00:00Z' },
      baseFilters,
    );

    expect(selected).toEqual({
      serviceCategories: ['Roads'],
      geographyLevel: 'ward',
      geographyValues: ['Ward 1'],
      timeRangeStart: '2026-03-02T00:00:00Z',
      timeRangeEnd: '2026-03-05T00:00:00Z',
    });

    const noPresetSelection = buildDefaultAutoSelection(
      {
        ...availability,
        byCategoryGeography: {
          Roads: { geographyLevels: [], geographyOptions: {} },
          Waste: { geographyLevels: [], geographyOptions: {} },
        },
        presets: [],
      },
      { start: '2026-03-01T00:00:00Z', end: '2026-03-10T00:00:00Z' },
      baseFilters,
    );

    expect(noPresetSelection).toEqual({
      serviceCategories: ['Roads'],
      geographyLevel: undefined,
      geographyValues: [],
      timeRangeStart: '2026-03-01T00:00:00Z',
      timeRangeEnd: '2026-03-10T00:00:00Z',
    });

    const fallbackOnly = buildDefaultAutoSelection(
      {
        ...availability,
        byCategoryGeography: {
          Roads: { geographyLevels: [], geographyOptions: {} },
          Waste: { geographyLevels: [], geographyOptions: {} },
        },
        presets: [],
      },
      { start: undefined, end: undefined },
      {
        ...baseFilters,
        timeRangeStart: '2026-03-09T00:00:00Z',
        timeRangeEnd: '2026-03-10T00:00:00Z',
      },
    );

    expect(fallbackOnly).toEqual({
      serviceCategories: ['Roads'],
      geographyLevel: undefined,
      geographyValues: [],
      timeRangeStart: '2026-03-09T00:00:00Z',
      timeRangeEnd: '2026-03-10T00:00:00Z',
    });
  });
});
