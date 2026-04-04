import { useEffect, useRef, useState } from 'react';
import { fetchCurrentForecastVisualization, fetchServiceCategoryOptions, submitVisualizationRenderEvent } from '../../../api/forecastVisualizations';
import { env } from '../../../config/env';
import type { ForecastProduct, ForecastVisualization, VisualizationRenderEvent } from '../../../types/forecastVisualization';

export function useForecastVisualization() {
  const [forecastProduct, setForecastProduct] = useState<ForecastProduct>(env.dashboardDefaultProduct);
  const [serviceCategories, setServiceCategories] = useState<string[]>([]);
  const [serviceCategoryOptions, setServiceCategoryOptions] = useState<string[]>([]);
  const [serviceCategoriesReady, setServiceCategoriesReady] = useState(false);
  const [visualization, setVisualization] = useState<ForecastVisualization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const reported = useRef<Record<string, boolean>>({});

  useEffect(() => {
    const controller = new AbortController();
    setServiceCategoriesReady(false);
    fetchServiceCategoryOptions(forecastProduct, controller.signal)
      .then((response) => {
        if (controller.signal.aborted) return;
        const nextOptions = response.categories;
        setServiceCategoryOptions(nextOptions);
        setServiceCategories((current) => {
          const filtered = current.filter((category) => nextOptions.includes(category));
          const next = filtered.length === nextOptions.length ? [] : filtered;
          return next.length === current.length && next.every((value, index) => value === current[index]) ? current : next;
        });
        setServiceCategoriesReady(true);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setServiceCategoryOptions([]);
          setServiceCategoriesReady(true);
        }
      });
    return () => controller.abort();
  }, [forecastProduct]);

  useEffect(() => {
    if (!serviceCategoriesReady) return;
    const controller = new AbortController();
    const allSelected = serviceCategories.length === 0;
    const excludedCategories = !allSelected && serviceCategories.length > serviceCategoryOptions.length / 2
      ? serviceCategoryOptions.filter((category) => !serviceCategories.includes(category))
      : [];
    const requestedCategories = allSelected || excludedCategories.length > 0 ? [] : serviceCategories;
    setIsLoading(true);
    setError(null);
    fetchCurrentForecastVisualization(forecastProduct, requestedCategories, excludedCategories, controller.signal)
      .then((response) => {
        setVisualization(response);
      })
      .catch((requestError: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(requestError.message);
        setVisualization(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, [forecastProduct, serviceCategories, serviceCategoriesReady, serviceCategoryOptions]);

  const reportRenderEvent = async (payload: VisualizationRenderEvent) => {
    if (!visualization) return;
    const key = `${visualization.visualizationLoadId}:${payload.renderStatus}`;
    if (reported.current[key]) return;
    reported.current[key] = true;
    await submitVisualizationRenderEvent(visualization.visualizationLoadId, payload);
  };

  return {
    forecastProduct,
    setForecastProduct,
    serviceCategories,
    setServiceCategories,
    serviceCategoryOptions,
    visualization,
    isLoading,
    error,
    reportRenderEvent,
  };
}
