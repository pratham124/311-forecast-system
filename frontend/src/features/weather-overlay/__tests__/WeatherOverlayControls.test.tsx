import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WeatherOverlayControls } from '../components/WeatherOverlayControls';

describe('WeatherOverlayControls', () => {
  it('toggles enable and changes measure', () => {
    const onEnabledChange = vi.fn();
    const onMeasureChange = vi.fn();
    const { rerender } = render(
      <WeatherOverlayControls
        enabled={false}
        selectedMeasure="temperature"
        onEnabledChange={onEnabledChange}
        onMeasureChange={onMeasureChange}
      />,
    );

    fireEvent.click(screen.getByLabelText('Enable weather overlay'));
    expect(onEnabledChange).toHaveBeenCalledWith(true);

    // Re-render with enabled=true
    rerender(
      <WeatherOverlayControls
        enabled={true}
        selectedMeasure="temperature"
        onEnabledChange={onEnabledChange}
        onMeasureChange={onMeasureChange}
        isOpen={true}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Snowfall' }));
    expect(onMeasureChange).toHaveBeenCalledWith('snowfall');

    // Re-render with selectedMeasure="snowfall"
    rerender(
      <WeatherOverlayControls
        enabled={true}
        selectedMeasure="snowfall"
        onEnabledChange={onEnabledChange}
        onMeasureChange={onMeasureChange}
        isOpen={true}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Precipitation' }));
    expect(onMeasureChange).toHaveBeenCalledWith('precipitation');
  });
});
