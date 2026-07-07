import React, { useEffect, useState } from 'react';
import { Globe } from 'lucide-react';
import PageWrapper from '../components/PageWrapper';
import { getInsights, type InsightsResponse } from '../services/api';

export default function Insights() {
  const [data, setData] = useState<InsightsResponse | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getInsights()
      .then((response) => {
        if (active) setData(response);
      })
      .catch((fetchError) => {
        if (active) setError(fetchError instanceof Error ? fetchError.message : 'Failed to load insights.');
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <PageWrapper>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Insights</h1>
          <p className="text-gray-500 mt-1">Live backend analytics for route cost, volume, and risk.</p>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>

        {!data && !error && (
          <div className="flex flex-col items-center justify-center min-h-[50vh] bg-white p-12 rounded-2xl shadow-sm border border-gray-200">
            <div className="w-16 h-16 bg-purple-100 text-[#7C6CF6] rounded-full flex items-center justify-center mb-6">
              <Globe className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading live insights</h2>
            <p className="text-gray-500">Fetching aggregated analytics from the FastAPI backend.</p>
          </div>
        )}

        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <section className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 lg:col-span-1">
              <h2 className="text-lg font-bold text-[#2D2A4A] mb-4">Cost Distribution</h2>
              <div className="space-y-4">
                {data.costDistribution.map((item) => (
                  <div key={item.name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">{item.name}</span>
                      <span className="font-semibold text-[#2D2A4A]">{item.value}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                      <div className="h-full rounded-full bg-[#6D5DF5]" style={{ width: `${item.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 lg:col-span-2">
              <h2 className="text-lg font-bold text-[#2D2A4A] mb-4">Top Routes</h2>
              <div className="space-y-4">
                {data.topRoutes.map((route) => (
                  <div key={route.path} className="flex items-center justify-between gap-4 rounded-xl border border-gray-100 p-4">
                    <div>
                      <div className="font-semibold text-[#2D2A4A]">{route.path}</div>
                      <div className="text-xs text-gray-500">Avg cost {route.avgCost}</div>
                    </div>
                    <div className="text-sm font-semibold text-gray-700">{route.volume}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 lg:col-span-3">
              <h2 className="text-lg font-bold text-[#2D2A4A] mb-4">Risk Heatmap</h2>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {data.riskHeatmap.map((item) => (
                  <div key={item.region} className="rounded-2xl bg-[#F8F6FC] p-4">
                    <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">{item.region}</div>
                    <div className="text-sm font-semibold text-[#2D2A4A] mt-2">{item.risk}</div>
                    <div className="text-xs text-gray-500 mt-1">Score {item.score}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}