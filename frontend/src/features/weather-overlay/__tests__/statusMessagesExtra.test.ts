import { describe, expect, it } from 'vitest';
import { getWeatherOverlayStatusMessage } from '../state/statusMessages';

describe('weather overlay status messages', () => {
  it('prefers server copy and falls back to the default message', () => {
    expect(getWeatherOverlayStatusMessage('disabled', 'Server says wait')).toBe('Server says wait');
    expect(getWeatherOverlayStatusMessage('visible')).toBe('Weather overlay is currently unavailable.');
  });
});
