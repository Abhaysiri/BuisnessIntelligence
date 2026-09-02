import React, { useState, useEffect } from 'react';
import { History, Search, ArrowRight, Activity, Clock } from 'lucide-react';

export default function AnalyticsHistory() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const resp = await fetch('http://127.0.0.1:8000/api/v1/audit/analytics-history');
      if (resp.ok) {
        const data = await resp.json();
        setHistory(data.history);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  return (
    <div className="p-8 flex flex-col h-[calc(100vh-4rem)] overflow-y-auto bg-slate-50">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <History className="text-blue-600" size={24} />
          Previous Analytics History
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Review past diagnostic payloads, KPI anomalies, and generated persona stories.
        </p>
      </div>

      <div className="grid gap-6">
        {history.length === 0 ? (
          <div className="p-8 text-center text-slate-500 bg-white border border-slate-200 rounded-xl">
            No analytics history found. Request a KPI story to generate logs.
          </div>
        ) : (
          history.map((item) => (
            <div key={item.id} className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col gap-4">
              <div className="flex justify-between items-start border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{item.story_headline || 'Untitled Analysis'}</h3>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500 font-medium">
                    <span className="flex items-center gap-1"><Activity size={14} className="text-emerald-600"/> KPI: {item.kpi_id || 'Unknown'}</span>
                    <span className="flex items-center gap-1"><Clock size={14} className="text-slate-400"/> {new Date(item.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <span className="px-2.5 py-1 bg-blue-100 text-blue-800 font-semibold rounded-md text-xs uppercase tracking-wider">
                  Role: {item.role}
                </span>
              </div>
              
              <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                {item.story_body}
              </div>
              
              {item.payload && (
                <div className="mt-2 p-3 bg-slate-50 rounded border border-slate-100 text-xs font-mono overflow-auto max-h-32 text-slate-600">
                  <div className="font-bold text-slate-500 mb-1">Diagnostic Payload Snippet:</div>
                  {JSON.stringify(JSON.parse(item.payload), null, 2)}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
