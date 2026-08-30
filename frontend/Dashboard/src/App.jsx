import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, History, Calendar, FileUp, Activity, BarChart2, MessageSquare, Send } from 'lucide-react';
import './App.css';

const domains = {
  Technical: ['Software Development', 'Cloud & DevOps', 'Data Science & Big Data', 'Artificial Intelligence & Machine Learning', 'Cybersecurity & Identity'],
  Sales: ['Vice President (VP) of Sales', 'Sales Development Representative', 'Sales Engineer', 'Sales Team Lead', 'Chief Revenue Officer (CRO)', 'Customer Success Manager (CSM)'],
  Media: ['Media Buyer', 'Media Planner', 'Content Strategist'],
  Marketing: ['Marketing Assistant / Coordinator', 'Social Media Coordinator', 'Content Marketer / Copywriter', 'Product Marketing Manager', 'Marketing Analytics Manager', 'Vice President (VP) of Marketing'],
  Other: ['Other Role']
};

function LoginPopup({ onLogin }) {
  const [step, setStep] = useState(1);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);

  const handleDomainClick = (domain) => {
    setSelectedDomain(domain);
    setStep(2);
  };

  const handleRoleClick = (role) => {
    setSelectedRole(role);
    onLogin(selectedDomain, role);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Welcome to BI Engine</h2>
        {step === 1 ? (
          <div>
            <h3>Which domain do you belong to?</h3>
            <div className="button-grid">
              {Object.keys(domains).map(domain => (
                <button key={domain} className="btn-primary" onClick={() => handleDomainClick(domain)}>
                  {domain}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <h3>Select your role in {selectedDomain}</h3>
            <div className="button-grid">
              {domains[selectedDomain].map(role => (
                <button key={role} className="btn-secondary" onClick={() => handleRoleClick(role)}>
                  {role}
                </button>
              ))}
            </div>
            <button className="btn-link" onClick={() => setStep(1)} style={{marginTop: '20px'}}>Back</button>
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
    { name: 'Dashboard Home', icon: <LayoutDashboard size={20} />, path: '/' },
    { name: 'Previous Analytics History', icon: <History size={20} />, path: '#' },
    { name: 'Major KPI Events', icon: <Calendar size={20} />, path: '#' },
    { name: 'Upload Documents', icon: <FileUp size={20} />, path: '#' },
    { name: 'Runtime Telemetry', icon: <Activity size={20} />, path: '#' },
    { name: 'Request KPI Story', icon: <BarChart2 size={20} />, path: '/kpi-analysis', highlight: true }
  ];

  return (
    <div className="sidebar">
      <div className="logo">BI Engine</div>
      <ul className="menu">
        {menuItems.map((item, idx) => (
          <li key={idx} 
              className={`menu-item ${location.pathname === item.path ? 'active' : ''} ${item.highlight ? 'highlight' : ''}`}
              onClick={() => item.path !== '#' && navigate(item.path)}>
            {item.icon}
            <span>{item.name}</span>
          </li>
        ))}
      </ul>
      
      <div className="telemetry-widget">
        <h4>Telemetry Preview</h4>
        <div className="t-row"><span>Latency:</span> <span>450ms</span></div>
        <div className="t-row"><span>Model Calls:</span> <span>12</span></div>
        <div className="t-row"><span>Token Usage:</span> <span>4.2k</span></div>
        <div className="t-row"><span>Est. Cost:</span> <span>$0.012</span></div>
      </div>
    </div>
  );
}

function Navbar({ userRole }) {
  return (
    <div className="navbar">
      <div className="nav-title">Business Intelligence Platform</div>
      <div className="user-profile">
        <div className="avatar">J</div>
        <div className="user-info">
          <span className="user-name">John</span>
          <span className="user-role">{userRole || 'Guest'}</span>
        </div>
      </div>
    </div>
  );
}

function Home() {
  return (
    <div className="page-content">
      <h2>Welcome to your Dashboard</h2>
      <p>Select options from the sidebar to navigate the BI Engine features.</p>
    </div>
  );
}

function KpiAnalysis() {
  return (
    <div className="page-content kpi-page">
      <h2>KPI Analysis & Storytelling</h2>
      <div className="reports-bar">
        <button className="report-btn">Daily KPI Report</button>
        <button className="report-btn">Weekly KPI Report</button>
        <button className="report-btn">Monthly KPI Report</button>
        <button className="report-btn">Custom Reports</button>
      </div>
      
      <div className="chat-container">
        <div className="chat-history">
          <div className="message system">
            Hello John! I am tuned to your persona. What KPI story would you like to investigate today?
          </div>
        </div>
        <div className="chat-input-area">
          <input type="text" placeholder="Enter your persona-specific prompt here..." className="chat-input" />
          <button className="chat-send"><Send size={20} /></button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState("");

  const handleLogin = (domain, role) => {
    setUserRole(role);
    setIsAuthenticated(true);
  };

  return (
    <Router>
      {!isAuthenticated && <LoginPopup onLogin={handleLogin} />}
      
      <div className="app-container">
        <Sidebar />
        <div className="main-area">
          <Navbar userRole={userRole} />
          <div className="scrollable-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/kpi-analysis" element={<KpiAnalysis />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}
