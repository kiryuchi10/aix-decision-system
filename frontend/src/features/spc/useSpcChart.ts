import { useEffect, useState } from 'react';
import { ApiError } from '../../app/apiClient';
import { ChartRequest, ChartResponse, postSpcChart } from './spc.api';

export function useSpcChart(req: ChartRequest) {
  const [data, setData] = useState<ChartResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);

    postSpcChart(req)
      .then((res) => {
        if (alive) setData(res);
      })
      .catch((e) => {
        if (alive) setError(e);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [JSON.stringify(req)]);

  return { data, loading, error };
}
