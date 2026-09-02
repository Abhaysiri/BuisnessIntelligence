import React, { useState, useEffect } from 'react';
import { Calendar, AlertTriangle, TrendingDown, TrendingUp } from 'lucide-react';

export default function MajorEvents() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const resp = await fetch('http://127.0.0.1:8000/api/v1/audit/major-events');
      if (resp.ok) {
        const data = await resp.json();
        setEvents(data.events);
      }
    } catch (e) {
      console.error("Failed to fetch major events", e);
    }
  };

  return (
    <div className="p-8 flex flex-col h-[calc(100vh-4rem)] overflow-y-auto bg-slate-50">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <Calendar className="text-rose-600" size={24} />
          Major KPI Events
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Significant KPI shifts (&gt;35% deviance from baseline) detected by the STL decomposition pipeline.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {events.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No major KPI events recorded.
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">KPI ID</th>
                <th className="px-6 py-3">Analysis Date</th>
                <th className="px-6 py-3">Observed Value</th>
                <th className="px-6 py-3">Expected Value</th>
                <th className="px-6 py-3">Severity</th>
                <th className="px-6 py-3">Z-Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {events.map((ev) => {
                const diff = ev.observed_value - ev.expected_value;
                const isDrop = diff < 0;
                return (
                  <tr key={ev.event_id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-bold text-slate-800">{ev.kpi_id}</td>
                    <td className="px-6 py-4 text-slate-600">{new Date(ev.analysis_end).toLocaleDateString()}</td>
                    <td className="px-6 py-4 font-semibold flex items-center gap-2">
                      {ev.observed_value.toFixed(2)}
                      {isDrop ? <TrendingDown size={14} className="text-rose-500" /> : <TrendingUp size={14} className="text-emerald-500" />}
                    </td>
                    <td className="px-6 py-4 text-slate-500">{ev.expected_value.toFixed(2)}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 rounded bg-rose-100 text-rose-800 text-xs font-bold flex items-center gap-1 w-max">
                        <AlertTriangle size={12} /> {ev.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-mono">{ev.z_score.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
