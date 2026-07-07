import React, { useState } from 'react';
import { Activity, ArrowRight, SlidersHorizontal } from 'lucide-react';
import PageWrapper from '../components/PageWrapper';
import { simulateScenario, type SimulationRequest, type SimulationResponse } from '../services/api';

export default function Simulation() {
  const [form, setForm] = useState<SimulationRequest>({
    amount: 100000,
    source_country: 'INDIA',
    destination_country: 'USA',
    purpose: 'INVESTMENT',
    business_size: 'LARGE',
    priority: 'COST',
    currency_handling: 'CONVERT',
    adjust_tax_pct: 5,
    adjust_fx_pct: 3,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState('');

  const runSimulation = async () => {
    setLoading(true);
    setError('');
    try {
      setResult(await simulateScenario(form));
    } catch (simulationError) {
      setError(simulationError instanceof Error ? simulationError.message : 'Simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Simulation</h1>
          <p className="text-gray-500 mt-1">Stress-test live route outcomes against tax and FX changes.</p>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 bg-white rounded-[2rem] p-8 shadow-sm border border-gray-100 space-y-6">
            <div className="flex items-center gap-3">
              <SlidersHorizontal className="w-5 h-5 text-[#6D5DF5]" />
              <h2 className="text-lg font-bold text-[#2D2A4A]">Scenario Inputs</h2>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Amount" type="number" value={form.amount} onChange={(value) => setForm((current) => ({ ...current, amount: Number(value) }))} />
              <Input label="Tax Adjustment %" type="number" value={form.adjust_tax_pct ?? 0} onChange={(value) => setForm((current) => ({ ...current, adjust_tax_pct: Number(value) }))} />
              <Input label="FX Adjustment %" type="number" value={form.adjust_fx_pct ?? 0} onChange={(value) => setForm((current) => ({ ...current, adjust_fx_pct: Number(value) }))} />
              <Select label="Priority" value={form.priority} onChange={(value) => setForm((current) => ({ ...current, priority: value }))} options={["COST", "TIME", "BALANCED"]} />
            </div>
            <button type="button" onClick={runSimulation} className="w-full bg-[#6D5DF5] hover:bg-[#5B4BE0] text-white py-4 rounded-full font-bold flex items-center justify-center gap-2 transition-colors shadow-md shadow-purple-500/20">
              Run Simulation <ArrowRight className="w-5 h-5" />
            </button>
          </div>

          <div className="lg:col-span-5 bg-[#F8F6FC] rounded-[2rem] p-8 shadow-sm border border-gray-100 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <Activity className="w-5 h-5 text-[#6D5DF5]" />
                <h2 className="text-lg font-bold text-[#2D2A4A]">Simulation Output</h2>
              </div>
              {!result && !loading && <p className="text-sm text-gray-500">Run a simulation to see the adjusted cost and risk profile.</p>}
              {loading && <p className="text-sm text-gray-500">Running simulation...</p>}
              {result && (
                <div className="space-y-4">
                  <ResultRow label="Route" value={result.route.path_display} />
                  <ResultRow label="Adjusted Tax" value={`$${result.simulation.adjusted_tax.toFixed(2)}`} />
                  <ResultRow label="Adjusted FX Loss" value={`$${result.simulation.adjusted_fx_loss.toFixed(2)}`} />
                  <ResultRow label="Compliance Cost" value={`$${result.simulation.compliance_cost.toFixed(2)}`} />
                  <ResultRow label="Total Cost" value={`$${result.simulation.total_cost_usd.toFixed(2)}`} />
                  <ResultRow label="Risk" value={result.simulation.risk_score} />
                </div>
              )}
            </div>

            <div className="mt-8 rounded-2xl bg-white p-5 border border-gray-100">
              <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Current Scenario</div>
              <div className="text-sm font-semibold text-[#2D2A4A] mt-2">{form.source_country} → {form.destination_country}</div>
              <div className="text-xs text-gray-500 mt-1">{form.purpose} · {form.business_size} · {form.currency_handling}</div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}

function Input({ label, value, onChange, type = 'text' }: { label: string; value: string | number; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className="w-full bg-[#F8F6FC] rounded-xl px-4 py-3 text-sm font-medium text-gray-900 border border-transparent focus:outline-none focus:ring-2 focus:ring-[#6D5DF5]/20" />
    </label>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return (
    <label className="block">
      <span className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="w-full bg-[#F8F6FC] rounded-xl px-4 py-3 text-sm font-medium text-gray-900 border border-transparent focus:outline-none focus:ring-2 focus:ring-[#6D5DF5]/20">
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </label>
  );
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-gray-200 pb-3 last:border-0 last:pb-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-bold text-[#2D2A4A] text-right">{value}</span>
    </div>
  );
}