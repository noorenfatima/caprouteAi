import React, { useEffect, useState } from 'react';
import { Network, PiggyBank, Gauge, ArrowUpRight, Activity, Zap, CheckCircle2, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from '../components/PageWrapper';
import { getDashboard, type DashboardResponse } from '../services/api';

export default function Overview() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState('');

  const handleDownloadReport = () => {
    const report = {
      generatedAt: new Date().toISOString(),
      summary: {
        totalRoutesAnalyzed: dashboard?.metrics.total_routes_analyzed ?? 0,
        avgCostReductionPct: dashboard?.metrics.avg_cost_reduction_pct ?? 0,
        efficiencyScore: dashboard?.metrics.efficiency_score ?? 0,
      },
      routes: dashboard?.recent_routes ?? [],
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'overview-report.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    let active = true;

    getDashboard()
      .then((data) => {
        if (active) {
          setDashboard(data);
          setError('');
        }
      })
      .catch((fetchError) => {
        if (active) {
          setError(fetchError instanceof Error ? fetchError.message : 'Failed to load dashboard data.');
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <PageWrapper>
      <div className="space-y-8">
        
        {/* HEADER */}
        <div>
          <h1 className="text-3xl font-bold text-[#2D2A4A] mb-2">Welcome back, Alex!</h1>
          <p className="text-gray-500 text-lg">Here's what's happening with your asset flows today.</p>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>

        {/* METRICS ROW */}
        <div className="grid grid-cols-3 gap-6">
          {/* Total Routes */}
          <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm relative overflow-hidden">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4">Total Routes Analyzed</div>
            <div className="flex items-baseline gap-3">
              <div className="text-4xl font-bold text-[#2D2A4A]">{dashboard?.metrics.total_routes_analyzed?.toLocaleString() ?? '...'}</div>
              <div className="flex items-center text-xs font-bold text-[#6D5DF5]">
                <Activity className="w-3 h-3 mr-1" />
                {dashboard?.metrics.avg_cost_reduction_pct?.toFixed(1) ?? '...'}%
              </div>
            </div>
            <Network className="absolute right-6 top-8 w-12 h-12 text-gray-100" strokeWidth={1.5} />
            <div className="mt-6 h-1 w-full bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-[#6D5DF5] w-[70%] rounded-full"></div>
            </div>
          </div>

          {/* Cost Reduction */}
          <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm relative overflow-hidden">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4">Avg Cost Reduction (%)</div>
            <div className="flex items-baseline gap-3">
              <div className="text-4xl font-bold text-[#2D2A4A]">{dashboard?.metrics.avg_cost_reduction_pct?.toFixed(1) ?? '...'}%</div>
              <div className="flex items-center text-xs font-bold text-[#6D5DF5]">
                <ArrowUpRight className="w-3 h-3 mr-1" />
                {dashboard?.metrics.avg_cost_reduction_pct ? `${Math.max(0, dashboard.metrics.avg_cost_reduction_pct - 16).toFixed(1)}%` : '...'}
              </div>
            </div>
            <PiggyBank className="absolute right-6 top-8 w-12 h-12 text-gray-100" strokeWidth={1.5} />
            <div className="mt-6 h-1 w-full bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-[#6D5DF5] w-[45%] rounded-full"></div>
            </div>
          </div>

          {/* Efficiency Score */}
          <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm relative overflow-hidden">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4">Efficiency Score</div>
            <div className="flex items-baseline gap-1">
              <div className="text-4xl font-bold text-[#6D5DF5]">{dashboard?.metrics.efficiency_score?.toFixed(0) ?? '...'}</div>
              <div className="text-xl font-bold text-gray-300">/100</div>
            </div>
            <Gauge className="absolute right-6 top-8 w-12 h-12 text-gray-100" strokeWidth={1.5} />
            <div className="mt-6 flex gap-1">
              <div className="h-1 flex-1 bg-[#6D5DF5] rounded-full"></div>
              <div className="h-1 flex-1 bg-[#6D5DF5] rounded-full"></div>
              <div className="h-1 flex-1 bg-[#6D5DF5] rounded-full"></div>
              <div className="h-1 flex-1 bg-[#6D5DF5] rounded-full"></div>
              <div className="h-1 flex-1 bg-gray-100 rounded-full"></div>
            </div>
          </div>
        </div>

        {/* MIDDLE ROW */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Chart Area */}
          <div className="lg:col-span-2 bg-[#F8F6FC] rounded-[2rem] p-8 relative overflow-hidden flex flex-col">
            <div className="flex justify-between items-start mb-12">
              <div>
                <h2 className="text-xl font-bold text-[#2D2A4A]">Asset Allocation Flow</h2>
                <p className="text-sm text-gray-500 mt-1">Real-time distribution across global nodes</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/matrix')}
                className="text-sm font-bold text-[#6D5DF5] bg-white px-4 py-2 rounded-full shadow-sm"
              >
                View Full Matrix
              </button>
            </div>

            {/* Abstract Chart */}
            <div className="flex-1 relative min-h-[200px]">
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                <path d="M0,80 Q20,90 40,60 T80,50 T100,60 L100,100 L0,100 Z" fill="url(#gradient)" opacity="0.5" />
                <path d="M0,80 Q20,90 40,60 T80,50 T100,60" fill="none" stroke="#6D5DF5" strokeWidth="2" />
                <defs>
                  <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6D5DF5" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#6D5DF5" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
              
              {/* Tooltip */}
              <div className="absolute top-[40%] left-[45%] bg-white rounded-xl p-3 shadow-lg border border-gray-100 transform -translate-x-1/2 -translate-y-1/2">
                <div className="text-[8px] font-bold text-[#6D5DF5] uppercase tracking-wider mb-1">Peak Efficiency</div>
                <div className="text-lg font-bold text-[#2D2A4A]">{dashboard?.metrics.efficiency_score?.toFixed(1) ?? '...'}%</div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Optimization Ready */}
            <div className="bg-[#6D5DF5] rounded-[2rem] p-8 text-white shadow-sm">
              <h3 className="text-lg font-bold mb-3">Optimization Ready</h3>
              <p className="text-sm text-white/80 leading-relaxed mb-6">
                The model is returning live route recommendations and cost comparisons.
              </p>
              <button
                type="button"
                onClick={() => navigate('/simulation')}
                className="w-full bg-white text-[#6D5DF5] py-3 rounded-full font-bold flex items-center justify-center gap-2 shadow-sm"
              >
                Run Simulation <Zap className="w-4 h-4 fill-current" />
              </button>
            </div>

            {/* Active Nodes */}
            <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm">
              <h3 className="text-sm font-bold text-[#2D2A4A] mb-6">Active Global Nodes</h3>
              <div className="space-y-4">
                {(dashboard?.active_nodes ?? ['Loading...']).map((node) => (
                  <div key={node} className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                      <span className="font-medium text-gray-700">{node}</span>
                    </div>
                    <span className="text-gray-500">Active</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM ROW */}
        <div className="bg-[#F8F6FC] rounded-[2rem] p-8">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-xl font-bold text-[#2D2A4A]">Recent Route Analysis</h2>
            <button
              type="button"
              onClick={handleDownloadReport}
              className="text-sm font-bold text-[#6D5DF5]"
            >
              Download Report
            </button>
          </div>

          <div className="w-full">
            <div className="grid grid-cols-12 text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4 px-4">
              <div className="col-span-2">ID</div>
              <div className="col-span-4">Destination</div>
              <div className="col-span-3 text-right">Cost Save</div>
              <div className="col-span-2 text-center">Score</div>
              <div className="col-span-1 text-right">Status</div>
            </div>

            <div className="space-y-3">
              {(dashboard?.recent_routes ?? []).map((route) => (
                <TableRow
                  key={route.id}
                  id={route.id}
                  dest={route.destination}
                  asset={route.asset_class}
                  save={route.cost_save}
                  score={route.score}
                  status={route.status === 'Active' ? 'success' : 'pending'}
                />
              ))}
            </div>
          </div>
        </div>

      </div>
    </PageWrapper>
  );
}

function TableRow({ id, dest, asset, save, score, status }: any) {
  return (
    <div className="grid grid-cols-12 items-center bg-white rounded-2xl p-4 shadow-sm border border-gray-50">
      <div className="col-span-2 text-sm text-gray-400 font-medium">{id}</div>
      <div className="col-span-4">
        <div className="text-sm font-bold text-[#2D2A4A]">{dest}</div>
        <div className="text-xs text-gray-500 mt-0.5">Asset Class: {asset}</div>
      </div>
      <div className="col-span-3 text-right text-sm font-bold text-green-600">
        {save !== 'Neutral' ? save : <span className="text-gray-400">{save}</span>}
      </div>
      <div className="col-span-2 text-center">
        <span className="text-xs font-bold text-[#6D5DF5] bg-[#EBE4FF] px-3 py-1 rounded-full">
          {score}
        </span>
      </div>
      <div className="col-span-1 flex justify-end">
        {status === 'success' ? (
          <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
          </div>
        ) : (
          <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
            <Clock className="w-4 h-4 text-gray-500" />
          </div>
        )}
      </div>
    </div>
  );
}
