/**
 * VPD Process Window: Heatmap (Temp x RH) + DOE overlay + target band + setpoint recommendation.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import * as echarts from 'echarts';
import {
  getVPDGrid,
  listVPDSettings,
  getRecommend,
  getOverlayPoints,
  getDOERunDetail,
  createVPDGrid,
} from '../api/vpd';
import type { VPDGridResponse, VPDSettingResponse, RecommendResponse, OverlayPoint, DOERunDetail } from '../types/vpd';
import { useAuth } from '../contexts/AuthContext';
import { AlertCircle, Target, Thermometer } from 'lucide-react';

const DEFAULT_GRID_PARAMS = {
  temp_min: 20,
  temp_max: 30,
  temp_step: 1,
  rh_min: 40,
  rh_max: 80,
  rh_step: 2,
};

export default function ProcessWindow() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const [gridId, setGridId] = useState<string | null>(null);
  const [grid, setGrid] = useState<VPDGridResponse | null>(null);
  const [settings, setSettings] = useState<VPDSettingResponse[]>([]);
  const [selectedSettingId, setSelectedSettingId] = useState<number | null>(null);
  const [recommend, setRecommend] = useState<RecommendResponse | null>(null);
  const [metricKey, setMetricKey] = useState('defect_rate');
  const [overlayPoints, setOverlayPoints] = useState<OverlayPoint[]>([]);
  const [viewMode, setViewMode] = useState<'both' | 'heatmap' | 'doe'>('both');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<DOERunDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedSetting = settings.find((s) => s.id === selectedSettingId);

  const loadGrid = useCallback(async (gid: string) => {
    try {
      const g = await getVPDGrid(gid);
      setGrid(g);
      return g;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load grid');
      return null;
    }
  }, []);

  const loadInitialGrid = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { grid_id } = await createVPDGrid(DEFAULT_GRID_PARAMS);
      setGridId(grid_id);
      await loadGrid(grid_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create grid');
    } finally {
      setLoading(false);
    }
  }, [loadGrid]);

  useEffect(() => {
    if (!isAuthenticated || authLoading) return;
    (async () => {
      try {
        const list = await listVPDSettings();
        setSettings(list);
        if (list.length && !selectedSettingId) setSelectedSettingId(list[0].id);
      } catch {
        // no settings yet
      }
    })();
  }, [isAuthenticated, authLoading]);

  useEffect(() => {
    if (!gridId) {
      loadInitialGrid();
      return;
    }
    loadGrid(gridId);
  }, [gridId, loadGrid]);

  useEffect(() => {
    if (!isAuthenticated || !gridId) return;
    getOverlayPoints({ metric_key: metricKey })
      .then((r) => setOverlayPoints(r.points))
      .catch(() => setOverlayPoints([]));
  }, [isAuthenticated, gridId, metricKey]);

  useEffect(() => {
    if (!selectedSettingId || !gridId) {
      setRecommend(null);
      return;
    }
    getRecommend(selectedSettingId, gridId)
      .then(setRecommend)
      .catch(() => setRecommend(null));
  }, [selectedSettingId, gridId]);

  useEffect(() => {
    if (!selectedRunId) {
      setRunDetail(null);
      return;
    }
    getDOERunDetail(selectedRunId).then(setRunDetail).catch(() => setRunDetail(null));
  }, [selectedRunId]);

  // ECharts: heatmap + scatter
  useEffect(() => {
    if (!chartRef.current || !grid) return;
    const temps = grid.temps;
    const rhs = grid.rhs;
    const matrix = grid.matrix;
    const heatmapData: [number, number, number][] = [];
    for (let i = 0; i < temps.length; i++) {
      for (let j = 0; j < rhs.length; j++) {
        heatmapData.push([i, j, matrix[i][j]]);
      }
    }
    const scatterData = overlayPoints.map((p) => [
      p.temp_c,
      p.rh_pct,
      p.metric_value,
      p.run_id,
      p.vpd_kpa,
    ]);

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }
    const opt: echarts.EChartsOption = {
      tooltip: {
        trigger: 'item',
        formatter: (p: unknown) => {
          const params = p as { seriesType?: string; data?: unknown[]; name?: string };
          if (params.seriesType === 'heatmap' && Array.isArray(params.data)) {
            const [xIdx, yIdx, vpd] = params.data as number[];
            const t = temps[xIdx];
            const r = rhs[yIdx];
            return `Temp: ${t}°C<br/>RH: ${r}%<br/>VPD: ${Number(vpd).toFixed(2)} kPa`;
          }
          if (params.seriesType === 'scatter' && Array.isArray(params.data)) {
            const [t, r, val, runId, vpd] = params.data as number[];
            return `Run: ${runId}<br/>Temp: ${t}°C<br/>RH: ${r}%<br/>VPD: ${Number(vpd).toFixed(2)} kPa<br/>${metricKey}: ${val}`;
          }
          return '';
        },
      },
      grid: { left: 60, right: 40, top: 40, bottom: 60 },
      xAxis: { type: 'category', data: temps.map(String), name: 'Temp (°C)' },
      yAxis: { type: 'category', data: rhs.map(String), name: 'RH (%)' },
      visualMap: {
        min: Math.min(...heatmapData.map((d) => d[2])),
        max: Math.max(...heatmapData.map((d) => d[2])),
        calculable: true,
        orient: 'vertical',
        right: 10,
        top: 'center',
        inRange: { color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'] },
      },
      series: [
        {
          name: 'VPD',
          type: 'heatmap',
          data: heatmapData,
          emphasis: { itemStyle: { borderColor: '#333', borderWidth: 1 } },
        },
        {
          name: 'DOE',
          type: 'scatter',
          data: scatterData,
          coordinateSystem: 'cartesian2d',
          xAxisIndex: 0,
          yAxisIndex: 0,
          symbolSize: (d: unknown) => {
            const arr = d as number[];
            const v = arr[2];
            return Math.max(6, Math.min(18, 6 + Math.abs(Number(v))));
          },
          itemStyle: { borderColor: '#fff', borderWidth: 1 },
        },
      ] as echarts.SeriesOption[],
    };
    // Scatter in category coords: map temp/rh to index for display
    const scatterMapped = scatterData.map((d) => {
      const temp: number = Number(d[0]);
      const rh: number = Number(d[1]);
      const tNum = (v: unknown) => Number(v);
      let xi = temps.findIndex((t) => Math.abs(tNum(t) - temp) < 0.01);
      if (xi < 0) {
        const idx = temps.reduce((a, t, i) => (Math.abs(tNum(t) - temp) < Math.abs(tNum(temps[a]) - temp) ? i : a), 0);
        xi = idx;
      }
      let yi = rhs.findIndex((r) => Math.abs(tNum(r) - rh) < 0.01);
      if (yi < 0) {
        const idx = rhs.reduce((a, r, i) => (Math.abs(tNum(r) - rh) < Math.abs(tNum(rhs[a]) - rh) ? i : a), 0);
        yi = idx;
      }
      return [xi, yi, d[2], d[3], d[4]];
    });
    type SeriesWithShow = echarts.SeriesOption & { show?: boolean; data?: unknown; encode?: unknown; dataMapping?: unknown };
    const seriesArr = opt.series as SeriesWithShow[];
    seriesArr[1].data = scatterMapped;
    seriesArr[0].show = viewMode !== 'doe';
    seriesArr[1].show = viewMode !== 'heatmap';
    chartInstance.current.setOption(opt as echarts.EChartsOption, true);

    const clickHandler = (params: unknown) => {
      const p = params as { seriesType?: string; data?: unknown[] };
      if (p.seriesType === 'scatter' && Array.isArray(p.data) && p.data[3] != null) {
        setSelectedRunId(String(p.data[3]));
      }
    };
    chartInstance.current.on('click', clickHandler);
    return () => {
      chartInstance.current?.off('click', clickHandler);
    };
  }, [grid, overlayPoints, viewMode, metricKey]);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="p-6 text-slate-400">
        {!isAuthenticated && 'Please log in to use Process Window.'}
        {authLoading && 'Loading...'}
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Target className="w-8 h-8 text-cyan-400" />
          Process Window (VPD)
        </h1>
        <p className="text-slate-400 mt-1">Temp × RH heatmap, DOE overlay, target band, recommended setpoint.</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-200 flex items-start gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-white">VPD Heatmap + DOE</h2>
            <div className="flex gap-2">
              <label className="text-slate-400 text-sm">View:</label>
              {(['both', 'heatmap', 'doe'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setViewMode(m)}
                  className={`px-2 py-1 rounded text-sm ${viewMode === m ? 'bg-cyan-600 text-white' : 'bg-slate-700 text-slate-300'}`}
                >
                  {m === 'both' ? 'Both' : m === 'heatmap' ? 'Heatmap' : 'DOE'}
                </button>
              ))}
            </div>
          </div>
          <div ref={chartRef} className="w-full h-[420px]" />
          {loading && <p className="text-slate-400 text-sm mt-2">Creating grid...</p>}
        </div>

        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <Target className="w-5 h-5 text-cyan-400" />
              Target band
            </h2>
            <label className="block text-sm text-slate-400 mb-1">Setting</label>
            <select
              value={selectedSettingId ?? ''}
              onChange={(e) => setSelectedSettingId(e.target.value ? Number(e.target.value) : null)}
              className="input-field w-full mb-3"
            >
              <option value="">Select</option>
              {settings.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            {selectedSetting && (
              <p className="text-slate-300 text-sm">
                VPD: {selectedSetting.target_min_kpa}–{selectedSetting.target_max_kpa} kPa
              </p>
            )}
          </div>

          <div className="card">
            <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <Thermometer className="w-5 h-5 text-amber-400" />
              Recommended setpoint
            </h2>
            {recommend?.temp_c != null ? (
              <div className="space-y-2 text-sm">
                <p className="text-white">Temp: <strong>{recommend.temp_c}°C</strong></p>
                <p className="text-white">RH: <strong>{recommend.rh_pct}%</strong></p>
                <p className="text-slate-300">VPD: {recommend.vpd_kpa?.toFixed(2)} kPa</p>
                <p className="text-slate-400">Margin: {recommend.margin?.toFixed(3)}</p>
                {recommend.sensitivity?.dVPD_dT != null && (
                  <p className="text-slate-400">dVPD/dT: {recommend.sensitivity.dVPD_dT}, dVPD/dRH: {recommend.sensitivity.dVPD_dRH}</p>
                )}
              </div>
            ) : (
              <p className="text-slate-400 text-sm">{recommend?.message || 'Select setting and grid.'}</p>
            )}
          </div>

          <div className="card">
            <h2 className="text-lg font-bold text-white mb-2">Metric</h2>
            <select
              value={metricKey}
              onChange={(e) => setMetricKey(e.target.value)}
              className="input-field w-full"
            >
              <option value="defect_rate">defect_rate</option>
              <option value="yield">yield</option>
            </select>
          </div>
        </div>
      </div>

      {selectedRunId && runDetail && (
        <div className="mt-6 card border border-cyan-700">
          <h3 className="text-lg font-bold text-white mb-2">Run: {runDetail.run_id}</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-400">Factors</p>
              <pre className="text-slate-300 bg-slate-800 p-2 rounded">{JSON.stringify(runDetail.factors, null, 2)}</pre>
            </div>
            <div>
              <p className="text-slate-400">Measurements</p>
              <ul className="text-slate-300">
                {runDetail.measurements.map((m) => (
                  <li key={m.metric_key}>{m.metric_key}: {m.metric_value} {m.unit || ''}</li>
                ))}
              </ul>
            </div>
          </div>
          <button type="button" onClick={() => setSelectedRunId(null)} className="mt-2 text-cyan-400 hover:underline text-sm">Close</button>
        </div>
      )}
    </div>
  );
}
