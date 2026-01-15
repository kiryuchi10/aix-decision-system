import { useEffect, useMemo, useState } from 'react';
import { ApiError } from '../../app/apiClient';
import { getProcessWindow, ProcessWindowRow } from './settings.api';

export function useProcessWindow() {
  const [rows, setRows] = useState<ProcessWindowRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getProcessWindow()
      .then((res) => {
        if (alive) setRows(res.rows);
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
  }, []);

  // key -> guardrail map
  const guardrails = useMemo(() => {
    const map = new Map<string, { hardMin: number; hardMax: number; unit?: string }>();
    (rows ?? []).forEach((r) => {
      map.set(r.key, { hardMin: r.hardMin, hardMax: r.hardMax, unit: r.unit });
    });
    return map;
  }, [rows]);

  return { rows, guardrails, loading, error };
}
