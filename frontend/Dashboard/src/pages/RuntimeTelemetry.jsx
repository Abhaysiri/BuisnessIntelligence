import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, Search, Filter, ChevronDown, ChevronRight, Terminal } from 'lucide-react';

export default function RuntimeTelemetry() {
  const [traces, setTraces] = useState([]);
  const [expandedGroups, setExpandedGroups] = useState({});

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchTelemetry = async () => {
    try {
      const resp = await fetch('http://127.0.0.1:8000/api/v1/audit/telemetry');
      if (resp.ok) {
        const data = await resp.json();
        setTraces(data.traces);
      }
    } catch (e) {
      console.error("Failed to fetch telemetry", e);
    }
  };

  const getStatusColor = (status) => {
    if (status === 'ERROR') return 'bg-rose-100 text-rose-800';
    if (status === 'OK') return 'bg-emerald-100 text-emerald-800';
    return 'bg-slate-100 text-slate-800';
  };

  const toggleGroup = (traceId) => {
    setExpandedGroups(prev => ({ ...prev, [traceId]: !prev[traceId] }));
  };

  const groupedTraces = React.useMemo(() => {
    const groups = {};
    traces.forEach(trace => {
      if (!groups[trace.trace_id]) {
        groups[trace.trace_id] = [];
      }
      groups[trace.trace_id].push(trace);
    });
    Object.values(groups).forEach(group => {
      group.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    });
    return Object.values(groups).sort((a, b) => new Date(b[0].start_time) - new Date(a[0].start_time));
  }, [traces]);

  const renderAttributes = (attrStr) => {
    try {
      const attrs = typeof attrStr === 'string' ? JSON.parse(attrStr) : attrStr;
      if (!attrs) return null;
      return Object.entries(attrs).map(([k, v]) => (
        <div key={k} className="inline-flex items-center gap-1 bg-slate-800 px-1.5 py-0.5 rounded text-[10px] mr-1 mb-1">
          <span className="text-slate-500">{k}:</span>
          <span className="text-slate-300 truncate max-w-[150px]">{String(v)}</span>
        </div>
      ));
    } catch {
      return <span className="text-xs">{attrStr}</span>;
    }
  };

  return (
    <div className="p-8 flex flex-col h-[calc(100vh-4rem)] overflow-y-auto bg-slate-900 text-slate-300">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Activity className="text-cyan-400" size={24} />
            Runtime Telemetry & Observability
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Live OpenTelemetry distributed traces and span logs exported directly from the KPI Engine.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Live Connection Active
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-lg overflow-hidden flex-1 flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/50 text-slate-400 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 w-10"></th>
                <th className="px-4 py-3 w-32">Timestamp</th>
                <th className="px-4 py-3">Span Name / Hierarchy</th>
                <th className="px-4 py-3 w-24">Status</th>
                <th className="px-4 py-3 w-24">Latency</th>
                <th className="px-4 py-3 w-[40%]">Attributes / Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {groupedTraces.map((group) => {
                const parent = group[0];
                const isExpanded = expandedGroups[parent.trace_id];
                const hasChildren = group.length > 1;
                
                const parentDuration = parent.end_time && parent.start_time 
                  ? ((new Date(parent.end_time) - new Date(parent.start_time))).toFixed(2)
                  : 'N/A';

                return (
                  <React.Fragment key={parent.trace_id}>
                    <tr className="hover:bg-slate-700/30 transition-colors cursor-pointer bg-slate-800/50" onClick={() => hasChildren && toggleGroup(parent.trace_id)}>
                      <td className="px-4 py-3">
                        {hasChildren && (
                          <div className="text-slate-400 hover:text-slate-200 transition-colors">
                            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{new Date(parent.start_time).toLocaleTimeString()}</td>
                      <td className="px-4 py-3 font-semibold text-slate-200 flex items-center gap-2">
                        <Terminal size={14} className="text-slate-500" />
                        {parent.name}
                        <span className="text-slate-600 font-normal text-[10px] ml-2">Trace: {parent.trace_id.substring(0, 8)}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded ${getStatusColor(parent.status_code)} font-bold`}>
                          {parent.status_code}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-amber-400/80">{parentDuration}ms</td>
                      <td className="px-4 py-3 text-slate-400">
                        {parent.status_code === 'ERROR' ? (
                          <span className="text-rose-400">{parent.status_description || 'Unknown Error'}</span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {renderAttributes(parent.attributes)}
                          </div>
                        )}
                      </td>
                    </tr>
                    
                    {isExpanded && group.slice(1).map((child) => {
                      const childDuration = child.end_time && child.start_time 
                        ? ((new Date(child.end_time) - new Date(child.start_time))).toFixed(2)
                        : 'N/A';
                      
                      return (
                        <tr key={child.id || child.span_id} className="hover:bg-slate-700/20 bg-slate-900/30 transition-colors">
                          <td className="px-4 py-3"></td>
                          <td className="px-4 py-3 text-slate-500 pl-8 text-[11px]">{new Date(child.start_time).toLocaleTimeString()}</td>
                          <td className="px-4 py-3 text-cyan-400/90 pl-8 flex items-center gap-2 border-l border-slate-700/50">
                            <div className="w-3 h-px bg-slate-700/50"></div>
                            {child.name}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded ${getStatusColor(child.status_code)} font-bold text-[10px]`}>
                              {child.status_code}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-amber-500/70 text-[11px]">{childDuration}ms</td>
                          <td className="px-4 py-3 text-slate-400">
                            {child.status_code === 'ERROR' ? (
                              <span className="text-rose-400 text-[11px]">{child.status_description || 'Unknown Error'}</span>
                            ) : (
                              <div className="flex flex-wrap gap-1">
                                {renderAttributes(child.attributes)}
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
          {traces.length === 0 && (
            <div className="p-12 text-center text-slate-500">
              Awaiting telemetry traces... Trigger pipeline actions to populate logs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
