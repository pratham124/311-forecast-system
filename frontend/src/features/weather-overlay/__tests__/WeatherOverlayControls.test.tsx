import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WeatherOverlayControls } from '../components/WeatherOverlayControls';

describe('WeatherOverlayControls', () => {
  it('toggles enable and changes measure', () => {
    const onEnabledChange = vi.fn();
    const onMeasureChange = vi.fn();
    render(
      <WeatherOverlayControls
        enabled={false}
        selectedMeasure="temperature"
        onEnabledChange={onEnabledChange}
        onMeasureChange={onMeasureChange}
      />,
    );

    fireEvent.click(screen.getByLabelText('Enable weather overlay'));
    expect(onEnabledChange).toHaveBeenCalledWith(true);

    fireEvent.change(screen.getByLabelText('Weather measure'), { target: { value: 'snowfall' } });
    expect(onMeasureChange).toHaveBeenCalledWith('snowfall');

    fireEvent.change(screen.getByLabelText('Weather measure'), { target: { value: 'precipitation' } });
    expect(onMeasureChange).toHaveBeenCalledWith('precipitation');
  });
});
