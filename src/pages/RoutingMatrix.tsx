import React, { useRef, useState } from 'react';
import { ArrowRight, CreditCard, SlidersHorizontal, Globe2, Shield, Zap as ZapIcon, Info, Sparkles, MapPinned, Brain, Volume2, Loader2, Square } from 'lucide-react';
import PageWrapper from '../components/PageWrapper';
import { API_BASE_URL, compareRoutes, explainRoute, getFXRisk, optimizeRoute, textToSpeech, type CompareResponse, type ExplainResponse, type FXRiskResponse, type OptimizeResponse, type RouteRequest } from '../services/api';

const inputStyles = 'w-full bg-white border-none rounded-xl px-4 py-3.5 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#6D5DF5]/20 shadow-sm';
const labelStyles = 'block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2';

export default function RoutingMatrix() {
  const [form, setForm] = useState<RouteRequest>({
    amount: 100000,
    source_country: 'INDIA',
    destination_country: 'USA',
    purpose: 'INVESTMENT',
    business_size: 'LARGE',
    priority: 'COST',
    currency_handling: 'CONVERT',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [fxRisk, setFxRisk] = useState<FXRiskResponse | null>(null);
  const [explanation, setExplanation] = useState('');
  const [explanationModel, setExplanationModel] = useState('');
  const [error, setError] = useState('');
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleStopTTS = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setTtsPlaying(false);
  };

  const handleTTS = async () => {
    if (ttsPlaying) {
      handleStopTTS();
      return;
    }
    if (!explanation || ttsLoading) return;
    setTtsLoading(true);
    try {
      const res = await textToSpeech(explanation);
      const audioSrc = `data:audio/wav;base64,${res.audio_base64}`;
      const audio = new Audio(audioSrc);
      audioRef.current = audio;
      audio.onended = () => {
        setTtsPlaying(false);
        audioRef.current = null;
      };
      audio.onerror = () => {
        setTtsPlaying(false);
        audioRef.current = null;
      };
      await audio.play();
      setTtsPlaying(true);
    } catch {
      // silently fail — button returns to idle
    } finally {
      setTtsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    setExplanation('');
    setExplanationModel('');
    try {
      const optimized = await optimizeRoute(form);
      const compared = await compareRoutes(form);
      const risk = optimized.fx_risk ?? await getFXRisk({ source_country: form.source_country, destination_country: form.destination_country });

      const explanationResponse: ExplainResponse = await explainRoute({
        source_country: form.source_country,
        destination_country: form.destination_country,
        amount: form.amount,
        purpose: form.purpose,
        recommended_path: optimized.recommended_route.path,
        total_cost_usd: optimized.recommended_route.total_cost_usd,
        total_time_hrs: optimized.recommended_route.total_time_hrs,
        compliance_score: optimized.recommended_route.compliance_score,
        fx_risk_score: risk.fx_risk_score,
        fx_risk_label: risk.risk_label,
        fx_interpretation: risk.interpretation,
      });

      setResult(optimized);
      setComparison(compared);
      setFxRisk(risk);
      setExplanation(explanationResponse.explanation);
      setExplanationModel(explanationResponse.model);
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageWrapper>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-[#2D2A4A] mb-2">{result ? 'Route Optimization Complete' : 'Route Parameters'}</h1>
          <p className="text-gray-500 text-lg">Define your capital movement corridor and analyze live backend output.</p>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>

        {!loading && !result && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="col-span-1 lg:col-span-8 space-y-6">
              <div className="bg-[#F8F6FC] rounded-[2rem] p-8">
                <div className="flex items-center gap-3 mb-6">
                  <CreditCard className="w-5 h-5 text-[#6D5DF5]" />
                  <h2 className="text-lg font-bold text-[#2D2A4A]">Core Inputs</h2>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className={labelStyles}>Amount</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6D5DF5] font-bold">$</span>
                      <input
                        className={`${inputStyles} pl-8 text-lg`}
                        type="number"
                        value={form.amount}
                        onChange={(event) => setForm((current) => ({ ...current, amount: Number(event.target.value) }))}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className={labelStyles}>Source Country</label>
                      <select className={inputStyles} value={form.source_country} onChange={(event) => setForm((current) => ({ ...current, source_country: event.target.value }))}>
                        <option value="INDIA">India</option>
                        <option value="USA">United States</option>
                        <option value="SINGAPORE">Singapore</option>
                        <option value="UAE">United Arab Emirates</option>
                        <option value="MAURITIUS">Mauritius</option>
                      </select>
                    </div>
                    <div>
                      <label className={labelStyles}>Destination Country</label>
                      <select className={inputStyles} value={form.destination_country} onChange={(event) => setForm((current) => ({ ...current, destination_country: event.target.value }))}>
                        <option value="USA">United States</option>
                        <option value="BRAZIL">Brazil</option>
                        <option value="GERMANY">Germany</option>
                        <option value="JAPAN">Japan</option>
                        <option value="SINGAPORE">Singapore</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-[#F8F6FC] rounded-[2rem] p-8">
                <div className="flex items-center gap-3 mb-6">
                  <SlidersHorizontal className="w-5 h-5 text-[#6D5DF5]" />
                  <h2 className="text-lg font-bold text-[#2D2A4A]">Context Inputs</h2>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className={labelStyles}>Purpose of Transfer</label>
                    <select className={inputStyles} value={form.purpose} onChange={(event) => setForm((current) => ({ ...current, purpose: event.target.value }))}>
                      <option value="EXPORT">Export</option>
                      <option value="SERVICE">Service</option>
                      <option value="INVESTMENT">Investment</option>
                      <option value="ROYALTY">Royalty</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelStyles}>Business Size</label>
                    <select className={inputStyles} value={form.business_size} onChange={(event) => setForm((current) => ({ ...current, business_size: event.target.value }))}>
                      <option value="SMALL">Small</option>
                      <option value="LARGE">Large</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelStyles}>Priority</label>
                    <select className={inputStyles} value={form.priority} onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}>
                      <option value="COST">Cost</option>
                      <option value="TIME">Time</option>
                      <option value="BALANCED">Balanced</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelStyles}>Currency Handling</label>
                    <select className={inputStyles} value={form.currency_handling} onChange={(event) => setForm((current) => ({ ...current, currency_handling: event.target.value }))}>
                      <option value="CONVERT">Convert</option>
                      <option value="HOLD">Hold</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 pt-4">
                <InfoCard title="190+ Jurisdictions" subtitle="Access local rails globally" icon={<Globe2 className="w-5 h-5 text-[#6D5DF5]" />} />
                <InfoCard title="Real-time KYC/AML" subtitle="Automated compliance checks" icon={<Shield className="w-5 h-5 text-[#6D5DF5]" />} />
                <InfoCard title="Instant Settlements" subtitle="T+0 delivery on major pairs" icon={<ZapIcon className="w-5 h-5 text-[#6D5DF5]" />} />
              </div>
            </div>

            <div className="col-span-1 lg:col-span-4">
              <div className="bg-[#F3E8FF] rounded-[2rem] p-8 h-full flex flex-col">
                <h2 className="text-xl font-bold text-[#2D2A4A] mb-8">Analysis Preview</h2>
                <div className="space-y-6 flex-1">
                  <PreviewRow label="Configured Route" value={`${form.source_country} → ${form.destination_country}`} caption={form.purpose} />
                  <PreviewRow label="Priority" value={form.priority} caption={form.currency_handling} />
                  <div className="bg-[#EBE4FF]/50 rounded-2xl p-5 flex gap-3 mt-8">
                    <Info className="w-5 h-5 text-[#6D5DF5] shrink-0" />
                    <p className="text-xs text-gray-600 font-medium leading-relaxed">The backend will compare direct, UAE, and Singapore routing based on your live parameters.</p>
                  </div>
                </div>

                <div className="mt-8">
                  <button type="button" onClick={handleAnalyze} className="w-full bg-[#6D5DF5] hover:bg-[#5B4BE0] text-white py-4 rounded-full font-bold flex items-center justify-center gap-2 transition-colors shadow-md shadow-purple-500/20">
                    Analyze Routes <ArrowRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-[2rem] shadow-sm p-20 flex flex-col items-center justify-center space-y-6 border border-gray-100">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-[#EBE4FF]"></div>
              <div className="w-16 h-16 rounded-full border-4 border-[#6D5DF5] border-t-transparent animate-spin absolute top-0 left-0"></div>
            </div>
            <p className="text-gray-600 font-medium">Analyzing global capital routes...</p>
          </div>
        )}

        {result && comparison && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="col-span-1 lg:col-span-7 flex flex-col gap-6">
              <div className="bg-white border border-gray-100 rounded-[2rem] p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <MapPinned className="w-5 h-5 text-[#6D5DF5]" />
                  <div>
                    <h3 className="text-lg font-bold text-[#2D2A4A]">Capital Flow Map</h3>
                    <p className="text-sm text-gray-500">Visual route of the calculated path and fallback corridors.</p>
                  </div>
                </div>
                {result.map_url ? (
                  <iframe
                    title="Capital Flow Map"
                    src={`${API_BASE_URL}${result.map_url}`}
                    className="w-full h-[420px] rounded-2xl border border-gray-100 bg-white"
                  />
                ) : (
                  <div className="h-[420px] rounded-2xl border border-dashed border-gray-200 flex items-center justify-center text-sm text-gray-500">
                    Map is unavailable for this analysis.
                  </div>
                )}
              </div>

              <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full bg-[#7C6CF6] flex items-center justify-center shadow-sm shadow-purple-500/20">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-[#2D2A4A]">Recommended Route</h3>
                    <p className="text-sm text-gray-500">{result.recommended_route.path_display}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                  <StatCard label="Cost" value={`$${result.recommended_route.total_cost_usd.toFixed(2)}`} />
                  <StatCard label="Time" value={`${result.recommended_route.total_time_hrs.toFixed(1)} hrs`} />
                  <StatCard label="Compliance" value={`${result.recommended_route.compliance_score.toFixed(0)}/100`} />
                  <StatCard label="Direct" value={result.direct_route.path_display} />
                </div>
              </div>

              <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm">
                <h3 className="text-lg font-bold text-[#2D2A4A] mb-6">Route Comparison</h3>
                <div className="space-y-3">
                  {comparison.routes.map((route) => (
                    <div key={route.path_display} className="rounded-2xl border border-gray-100 p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                      <div>
                        <div className="font-bold text-[#2D2A4A]">{route.path_display}</div>
                        <div className="text-xs text-gray-500">{route.label}</div>
                      </div>
                      <div className="text-sm text-gray-600">${route.total_cost_usd.toFixed(2)} · {route.total_time_hrs.toFixed(1)}h · {route.compliance_score.toFixed(0)}/100</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="col-span-1 lg:col-span-5 flex flex-col gap-6">
              <div className="bg-[#6D5DF5] rounded-[2rem] p-8 text-white shadow-sm">
                <h3 className="text-lg font-bold mb-3">Analysis Summary</h3>
                <p className="text-sm text-white/80 leading-relaxed mb-6">The backend engine selected the route that best matches your priority and compliance profile.</p>
                <button type="button" onClick={() => setResult(null)} className="w-full bg-white text-[#6D5DF5] py-3 rounded-full font-bold">Run another analysis</button>
              </div>

              <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Brain className="w-5 h-5 text-[#6D5DF5]" />
                    <div>
                      <h3 className="text-lg font-bold text-[#2D2A4A]">AI Explanation</h3>
                      <p className="text-sm text-gray-500">Model: {explanationModel || 'pending'}</p>
                    </div>
                  </div>
                  {explanation && (
                    <button
                      type="button"
                      onClick={handleTTS}
                      disabled={ttsLoading}
                      title={ttsPlaying ? 'Stop playback' : 'Listen to explanation'}
                      className={`group relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 ${
                        ttsPlaying
                          ? 'bg-red-50 text-red-500 hover:bg-red-100'
                          : ttsLoading
                          ? 'bg-[#F8F6FC] text-[#6D5DF5] cursor-wait'
                          : 'bg-[#F8F6FC] text-[#6D5DF5] hover:bg-[#EBE4FF] hover:scale-110'
                      } shadow-sm`}
                    >
                      {ttsLoading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : ttsPlaying ? (
                        <Square className="w-4 h-4 fill-current" />
                      ) : (
                        <Volume2 className="w-5 h-5" />
                      )}
                    </button>
                  )}
                </div>
                <p className="text-sm leading-7 text-gray-700 whitespace-pre-line">
                  {explanation || 'Generating explanation...'}
                </p>
                {fxRisk && (
                  <div className="mt-6 rounded-2xl bg-[#F8F6FC] p-4">
                    <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">FX Risk</div>
                    <div className="mt-1 text-sm font-semibold text-[#2D2A4A]">{fxRisk.risk_label} · {fxRisk.fx_risk_score.toFixed(1)}/100</div>
                    <div className="text-xs text-gray-500 mt-2">{fxRisk.interpretation}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}

function InfoCard({ title, subtitle, icon }: { title: string; subtitle: string; icon: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5 flex items-center gap-4 shadow-sm">
      <div className="w-10 h-10 rounded-full bg-[#F8F6FC] flex items-center justify-center shrink-0">{icon}</div>
      <div>
        <div className="text-sm font-bold text-[#2D2A4A]">{title}</div>
        <div className="text-[10px] text-gray-500 mt-0.5">{subtitle}</div>
      </div>
    </div>
  );
}

function PreviewRow({ label, value, caption }: { label: string; value: string; caption?: string }) {
  return (
    <div className="flex justify-between items-start">
      <span className="text-sm text-gray-500 font-medium">{label}</span>
      <div className="text-right">
        <div className="text-sm font-bold text-[#2D2A4A]">{value}</div>
        {caption && <div className="text-[10px] font-bold text-[#6D5DF5] uppercase tracking-wider mt-1">{caption}</div>}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#F8F6FC] rounded-2xl p-4">
      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{label}</div>
      <div className="text-sm font-semibold text-[#2D2A4A] mt-2 break-words">{value}</div>
    </div>
  );
}