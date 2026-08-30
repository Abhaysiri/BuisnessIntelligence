import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  History, 
  Calendar, 
  FileUp, 
  Activity, 
  BarChart2, 
  Send, 
  ChevronRight,
  ChevronDown,
  ArrowLeft,
  Sparkles
} from 'lucide-react';
import './index.css';

const domains = {
  Technical: [
    'Software Development', 
    'Cloud & DevOps', 
    'Data Science & Big Data', 
    'Artificial Intelligence & Machine Learning', 
    'Cybersecurity & Identity'
  ],
  Sales: [
    'Vice President (VP) of Sales', 
    'Sales Development Representative', 
    'Sales Engineer', 
    'Sales Team Lead', 
    'Chief Revenue Officer (CRO)', 
    'Customer Success Manager (CSM)'
  ],
  Media: [
    'Media Buyer', 
    'Media Planner', 
    'Content Strategist'
  ],
  Marketing: [
    'Marketing Assistant / Coordinator', 
    'Social Media Coordinator', 
    'Content Marketer / Copywriter', 
    'Product Marketing Manager', 
    'Marketing Analytics Manager', 
    'Vice President (VP) of Marketing'
  ],
  Other: [
    'Operations Lead', 
    'Business Analyst', 
    'Product Manager'
  ]
};

function LoginPopup({ onLogin }) {
  const [step, setStep] = useState(1);
  const [selectedDomain, setSelectedDomain] = useState(null);

  const handleDomainClick = (domain) => {
    setSelectedDomain(domain);
    setStep(2);
  };

  const handleRoleClick = (role) => {
    onLogin(selectedDomain, role);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 p-8 max-w-lg w-full transition-all">
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-blue-50 text-blue-600 mb-3">
            <BarChart2 size={22} />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Welcome to BI Engine</h2>
          <p className="text-sm text-slate-500 mt-1">
            {step === 1 ? 'Select your primary domain to personalize your analytical workspace' : `Select your role within ${selectedDomain}`}
          </p>
        </div>

        {step === 1 ? (
          <div className="space-y-2">
            {Object.keys(domains).map((domain) => (
              <button
                key={domain}
                onClick={() => handleDomainClick(domain)}
                className="w-full text-left px-4 py-3 rounded-lg border border-slate-200 hover:border-blue-600 hover:bg-blue-50/40 text-slate-800 font-medium transition-all duration-200 flex items-center justify-between group cursor-pointer"
              >
                <span>{domain}</span>
                <ChevronRight size={18} className="text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
              </button>
            ))}
          </div>
        ) : (
          <div>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {domains[selectedDomain].map((role) => (
                <button
                  key={role}
                  onClick={() => handleRoleClick(role)}
                  className="w-full text-left px-4 py-2.5 rounded-lg border border-slate-200 hover:border-blue-600 hover:bg-blue-50/40 text-slate-800 text-sm font-medium transition-all duration-200 cursor-pointer"
                >
                  {role}
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(1)}
              className="mt-5 text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <ArrowLeft size={14} /> Back to domains
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard Home', icon: <LayoutDashboard size={18} />, path: '/' },
    { name: 'Previous Analytics History', icon: <History size={18} />, path: '#' },
    { name: 'Major KPI Events', icon: <Calendar size={18} />, path: '#' },
    { name: 'Upload Documents', icon: <FileUp size={18} />, path: '#' },
    { name: 'Runtime Telemetry', icon: <Activity size={18} />, path: '#' },
    { name: 'Request KPI Story', icon: <BarChart2 size={18} />, path: '/kpi-analysis' }
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen shrink-0 select-none border-r border-slate-800">
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
            BI
          </div>
          <span className="text-base font-bold tracking-tight text-white">BI Engine</span>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <div
              key={item.name}
              onClick={() => item.path !== '#' && navigate(item.path)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'bg-slate-800 text-white border-l-4 border-blue-500 pl-2 rounded-l-none'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <span className={isActive ? 'text-blue-400' : 'text-slate-400'}>{item.icon}</span>
              <span>{item.name}</span>
            </div>
          );
        })}
      </nav>
    </aside>
  );
}

function Navbar({ userRole }) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
      <h1 className="text-base font-semibold text-slate-900 tracking-tight">
        Business Intelligence Platform
      </h1>
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-sm flex items-center justify-center">
          J
        </div>
        <div className="flex flex-col text-right leading-tight">
          <span className="text-sm font-semibold text-slate-900">John</span>
          <span className="text-xs text-slate-500">{userRole || 'Software Development'}</span>
        </div>
      </div>
    </header>
  );
}

function Home() {
  return (
    <div className="p-8">
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-xs max-w-3xl">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Welcome to your Dashboard</h2>
        <p className="text-slate-600 text-sm leading-relaxed">
          Select <strong className="text-slate-800 font-semibold">Request KPI Story</strong> from the left sidebar to analyze KPI anomalies, inspect underlying metric drivers, and generate tailored persona narratives.
        </p>
      </div>
    </div>
  );
}

function KpiAnalysis() {
  const [inputText, setInputText] = useState('');

  const reportFilters = [
    { label: 'Daily KPI Report', detail: 'Last 24 Hours' },
    { label: 'Weekly KPI Report', detail: 'Trailing 7 Days' },
    { label: 'Monthly KPI Report', detail: 'Current Month (MTD)' },
    { label: 'Custom Reports', detail: 'Date Range & Metrics' }
  ];

  return (
    <div className="p-8 flex flex-col h-[calc(100vh-4rem)] overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
          KPI Analysis & Storytelling
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Real-time diagnostic storytelling powered by deterministic analytics and LangGraph orchestration.
        </p>
      </div>

      {/* 4 Clean Filter / Action Cards styled as input/dropdown triggers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {reportFilters.map((report) => (
          <button
            key={report.label}
            className="bg-white border border-slate-200 rounded-lg p-3.5 text-left hover:border-slate-300 hover:shadow-xs transition-all duration-200 flex items-center justify-between group cursor-pointer"
          >
            <div>
              <div className="text-sm font-semibold text-slate-800 group-hover:text-blue-600 transition-colors">
                {report.label}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">{report.detail}</div>
            </div>
            <ChevronDown size={16} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
          </button>
        ))}
      </div>

      {/* Chat Interface Container */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs flex-1 flex flex-col min-h-[440px] overflow-hidden">
        {/* Chat Header */}
        <div className="px-6 py-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-blue-600" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Interactive Storyteller Session
            </span>
          </div>
          <span className="text-xs text-slate-400 font-medium">Ready</span>
        </div>

        {/* Chat History */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          <div className="flex items-start gap-3 max-w-2xl">
            <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 mt-1 font-semibold text-xs">
              AI
            </div>
            <div className="bg-blue-50 text-blue-900 border border-blue-100 rounded-2xl rounded-tl-xs p-4 text-sm leading-relaxed shadow-xs">
              Hello John! I am tuned to your persona. What KPI story would you like to investigate today? You can ask about recent variance anomalies, dimensional breakdowns, or conversion drivers.
            </div>
          </div>
        </div>

        {/* Input Field Area */}
        <div className="p-4 border-t border-slate-200 bg-white">
          <form 
            onSubmit={(e) => { e.preventDefault(); setInputText(''); }}
            className="relative flex items-center"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter your persona-specific prompt here..."
              className="w-full bg-slate-50 border border-slate-300 rounded-full pl-5 pr-14 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 focus:bg-white transition-all duration-200"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center transition-all duration-200 shadow-xs cursor-pointer"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [userRole, setUserRole] = useState('Software Development');

  const handleLogin = (domain, role) => {
    setUserRole(role);
    setIsAuthenticated(true);
  };

  return (
    <Router>
      {!isAuthenticated && <LoginPopup onLogin={handleLogin} />}

      <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Navbar userRole={userRole} />
          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/kpi-analysis" element={<KpiAnalysis />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

