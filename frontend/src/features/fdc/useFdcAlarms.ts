import { useEffect, useState } from 'react';
import { ApiError } from '../../app/apiClient';
import { Alarm, ProcessCapability, getActiveAlarms, getFdcProcessCapability } from './fdc.api';

export function useFdc() {
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [cap, setCap] = useState<ProcessCapability | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let alive = true;
    async function run() {
      try {
        setLoading(true);
        const [a, c] = await Promise.all([getActiveAlarms(), getFdcProcessCapability()]);
        if (!alive) return;
        setAlarms(a);
        setCap(c);
      } catch (e: any) {
        if (!alive) return;
        setError(e);
      } finally {
        if (alive) setLoading(false);
      }
    }
    run();
    const t = setInterval(run, 4000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  return { alarms, cap, loading, error };
}
