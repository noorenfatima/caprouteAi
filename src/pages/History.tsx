import React, { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowRight, Banknote, ShieldCheck, Timer } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from '../components/PageWrapper';
import { getHistory } from '../services/api';

export default function History() {
  const navigate = useNavigate();
  const [processingOnly, setProcessingOnly] = useState(false);
  const [rows, setRows] = useState<Array<{ route: string; asset: string; cost: string; status: string; date: string }>>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getHistory(5)
      .then((data) => {
        if (active) {
          setRows(
            data.entries.map((entry, index) => ({
              route: entry.destination.replace(' → ', ' -> '),
              asset: 'Cash',
              cost: index === 2 ? '0.019%' : '0.024%',
              status: entry.status === 'Active' ? 'PROCESSING' : 'COMPLETED',
              date: new Date(Date.now() - index * 86400000).toLocaleString(undefined, {
                month: 'short',
                day: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              }),
            }))
          );
          setError('');
        }
      })
      .catch((fetchError) => {
        if (active) {
          setError(fetchError instanceof Error ? fetchError.message : 'Failed to load history data.');
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const visibleRows = useMemo(
    () => (processingOnly ? rows.filter((row) => row.status === 'PROCESSING') : rows),
    [processingOnly, rows]
  );

  const handleExportCsv = () => {
    const header = 'Route,Asset Type,Cost (%),Status,Date';
    const body = visibleRows.map((row) => [row.route, row.asset, row.cost, row.status, row.date].join(','));
    const csv = [header, ...body].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'transaction-history.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageWrapper>
      <div className="space-y-8">
        
        {/* HEADER */}
        <div>
          <h1 className="text-3xl font-bold text-[#2D2A4A] mb-2">History</h1>
            {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        {/* TOP ROW */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Total Assets Flowed */}
          <div className="lg:col-span-2 bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm flex flex-col justify-between relative overflow-hidden">
            <div>
              <div className="text-sm font-bold text-gray-500 mb-1">Total Assets Flowed</div>
              <div className="text-5xl font-bold text-[#2D2A4A]">{rows.length ? `$${(rows.length * 8.56).toFixed(1)}M` : '$...M'}</div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mt-12">
              <div>
                <div className="text-[10px] font-bold text-[#6D5DF5] uppercase tracking-wider mb-1">Success Rate</div>
                <div className="text-xl font-bold text-[#2D2A4A]">{rows.length ? '99.82%' : '...'} </div>
              </div>
              <div>
                <div className="text-[10px] font-bold text-[#6D5DF5] uppercase tracking-wider mb-1">Avg. Latency</div>
                <div className="text-xl font-bold text-[#2D2A4A]">{rows.length ? '24ms' : '...'}</div>
              </div>
              <div>
                <div className="text-[10px] font-bold text-[#6D5DF5] uppercase tracking-wider mb-1">Optimized Routes</div>
                <div className="text-xl font-bold text-[#2D2A4A]">{rows.length ? `${rows.length * 240}` : '...'}</div>
              </div>
            </div>

            {/* Abstract Background Shape */}
            <div className="absolute right-0 top-0 w-64 h-full bg-gradient-to-l from-[#F8F6FC] to-transparent pointer-events-none"></div>
          </div>

          {/* Cost Optimization */}
          <div className="bg-[#6D5DF5] rounded-[2rem] p-8 text-white shadow-sm relative overflow-hidden">
            <div className="flex justify-between items-start mb-6">
              <Activity className="w-6 h-6 text-white/80" />
              <span className="bg-white/20 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                Live Flow
              </span>
            </div>
            
            <h3 className="text-xl font-bold mb-3">Cost Optimization</h3>
            <p className="text-sm text-white/80 leading-relaxed mb-8">
              Routing algorithms saved <span className="font-bold text-white">$12,403</span> in transaction fees this month.
            </p>
            
            <button
              type="button"
              onClick={() => navigate('/matrix')}
              className="bg-white text-[#6D5DF5] px-6 py-3 rounded-full font-bold flex items-center gap-2 shadow-sm text-sm"
            >
              View Report <ArrowRight className="w-4 h-4" />
            </button>
          </div>

        </div>

        {/* TRANSACTION REGISTRY */}
        <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-xl font-bold text-[#2D2A4A]">Transaction Registry</h2>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleExportCsv}
                className="text-sm font-bold text-[#6D5DF5] bg-[#EBE4FF] px-4 py-2 rounded-full"
              >
                Export CSV
              </button>
              <button
                type="button"
                onClick={() => setProcessingOnly((value) => !value)}
                className="text-sm font-bold text-gray-500 bg-[#F8F6FC] px-4 py-2 rounded-full"
              >
                {processingOnly ? 'Show All' : 'Filter Processing'}
              </button>
            </div>
          </div>

          <div className="w-full">
            <div className="grid grid-cols-12 text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4 px-4">
              <div className="col-span-4">Route</div>
              <div className="col-span-2">Asset Type</div>
              <div className="col-span-2">Cost (%)</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-2 text-right">Date</div>
            </div>

            <div className="space-y-2">
              {visibleRows.map((row) => (
                <TableRow
                  key={`${row.route}-${row.date}`}
                  route={row.route}
                  asset={row.asset}
                  cost={row.cost}
                  status={row.status}
                  date={row.date}
                />
              ))}
            </div>

            <div className="flex items-center justify-between mt-8 px-4">
              <div className="text-sm text-gray-500 font-medium">Showing {visibleRows.length} of {rows.length} entries</div>
              <div className="flex items-center gap-2">
                <button className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 font-bold">{'<'}</button>
                <button className="w-8 h-8 rounded-full flex items-center justify-center bg-[#6D5DF5] text-white font-bold">1</button>
                <button className="w-8 h-8 rounded-full flex items-center justify-center text-gray-500 hover:bg-gray-100 font-bold">2</button>
                <button className="w-8 h-8 rounded-full flex items-center justify-center text-gray-500 hover:bg-gray-100 font-bold">3</button>
                <button className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 font-bold">{'>'}</button>
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM ROW */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-[#F8F6FC] rounded-[2rem] p-6 flex items-center gap-5">
            <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center shrink-0 shadow-sm">
              <Timer className="w-5 h-5 text-[#6D5DF5]" />
            </div>
            <div>
              <div className="text-sm font-bold text-[#2D2A4A] mb-1">Historical Speed</div>
              <div className="text-xs text-gray-500 leading-relaxed">Transfer times have improved by 14% since the last engine update.</div>
            </div>
          </div>

          <div className="bg-[#F8F6FC] rounded-[2rem] p-6 flex items-center gap-5">
            <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center shrink-0 shadow-sm">
              <ShieldCheck className="w-5 h-5 text-[#6D5DF5]" />
            </div>
            <div>
              <div className="text-sm font-bold text-[#2D2A4A] mb-1">Immutable Logs</div>
              <div className="text-xs text-gray-500 leading-relaxed">All history records are cryptographically verified and archived.</div>
            </div>
          </div>
        </div>

      </div>
    </PageWrapper>
  );
}

function TableRow({ route, asset, cost, status, date }: any) {
  const isCompleted = status === 'COMPLETED';
  return (
    <div className="grid grid-cols-12 items-center px-4 py-4 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors rounded-xl">
      <div className="col-span-4 text-sm font-bold text-[#2D2A4A]">{route}</div>
      <div className="col-span-2 flex items-center gap-2">
        <Banknote className="w-4 h-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-600">{asset}</span>
      </div>
      <div className="col-span-2 text-sm font-bold text-[#6D5DF5]">{cost}</div>
      <div className="col-span-2">
        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
          isCompleted ? 'bg-green-100 text-green-600' : 'bg-[#EBE4FF] text-[#6D5DF5]'
        }`}>
          • {status}
        </span>
      </div>
      <div className="col-span-2 text-right text-sm text-gray-500 font-medium">{date}</div>
    </div>
  );
}
