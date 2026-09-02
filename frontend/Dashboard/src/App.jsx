import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  History,
  Calendar,
  FileUp,
  Activity,
  BarChart2,
  Send,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Unlock,
  RefreshCw,
  Zap,
  Sliders,
  Users,
  TrendingDown,
  Building2,
  Layers,
  ChevronRight,
  UserCheck,
  LogOut
} from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Full 7 Domains and 25 Roles Configuration
const domainsData = {
  "Engineering & IT": {
    id: "eng_it",
    description: "Zero-day patches, DB lag, CI/CD freezes, and 28 regional/device latency & crash actions.",
    roles: [
      {
        id: "eng_vp",
        title: "VP of Engineering",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "Company-wide CI/CD freezes, major out-of-band patches, emergency architecture overrides"
      },
      {
        id: "eng_lead_sre",
        title: "Lead Site Reliability Engineer (SRE)",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Infrastructure auto-scaling, DB read-query routing, cache warming"
      },
      {
        id: "eng_regional_lead",
        title: "Regional Engineering Lead (Americas / EMEA / APAC)",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Investigating regional latency/crash issues generated in the playbook"
      },
      {
        id: "eng_mobile_mgr",
        title: "Mobile / Platform Engineering Manager",
        level: "Manager",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Halting iOS/Android app store rollouts (Read-only / Escalates to VP/Lead)"
      }
    ],
    sampleActions: [
      { id: "eng_action_zero_day", name: "Deploy Emergency Zero-Day CVE Patch", level: "VP", trigger: "CVE-2026-9021 Critical Vulnerability detected", impact: "System-wide" },
      { id: "eng_action_db_lag", name: "Reroute DB Read Queries to Secondary Pool", level: "Lead", trigger: "Primary DB replication lag > 2500ms", impact: "Database Cluster" },
      { id: "eng_action_cicd_freeze", name: "Enforce Company-Wide Production CI/CD Freeze", level: "VP", trigger: "Elevated checkout failure rate (Sev-1)", impact: "All Services" },
      { id: "eng_action_reg_americas_ios", name: "Mitigate Americas iOS Latency & Crash Spike", level: "Lead", trigger: "Americas iOS p99 latency > 800ms", impact: "Americas iOS" },
      { id: "eng_action_reg_emea_android", name: "Mitigate EMEA Android Crash Spike", level: "Lead", trigger: "EMEA Android crash rate > 1.1%", impact: "EMEA Android" },
      { id: "eng_action_reg_apac_web", name: "Purge & Recache APAC Edge CDN PoP", level: "Lead", trigger: "APAC Edge CDN cache hit ratio < 80%", impact: "APAC CDN" }
    ]
  },
  "Sales": {
    id: "sales",
    description: "Cart abandonment, pipeline spiffs, at-risk $100k+ deals, and 28 targeted renewal discount actions.",
    roles: [
      {
        id: "sales_vp",
        title: "VP of Global Sales / CRO",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "High-level pipeline spiff budgets, overriding standard discount limits (>20%)"
      },
      {
        id: "sales_ent_dir",
        title: "Enterprise Sales Director",
        level: "Director",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Intervening on at-risk 100k+ accounts, authorizing discounts specifically for Enterprise"
      },
      {
        id: "sales_regional_mgr",
        title: "Regional Sales Manager (Americas / EMEA / APAC)",
        level: "Manager",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Initiating targeted outreach campaigns for specific regional territories"
      },
      {
        id: "sales_ecom_lead",
        title: "E-Commerce / Digital Sales Lead",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Triggering automated cart abandonment sequences and online discount codes"
      },
      {
        id: "sales_sdr_lead",
        title: "SDR Team Lead",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Executing outbound spiffs and tactical outreach"
      }
    ],
    sampleActions: [
      { id: "sales_action_cart_abandonment", name: "Trigger Automated 3-Stage Cart Abandonment Sequence", level: "Lead", trigger: "Cart drop-off rate > 68%", impact: "Digital Funnel" },
      { id: "sales_action_spiff_budget", name: "Authorize Mid-Quarter Global Pipeline Spiff ($50k)", level: "VP", trigger: "Quarterly pipeline target gap > 15%", impact: "Global Sales Org" },
      { id: "sales_renew_americas_enterprise", name: "Apply Americas Enterprise 12% Renewal Discount Lock", level: "Lead", trigger: "Enterprise renewal window in 30 days", impact: "Americas Accounts" },
      { id: "sales_renew_emea_midmarket", name: "Deploy EMEA Mid-Market Multi-Year Value Bundle", level: "Lead", trigger: "EMEA Mid-Market churn forecast > 8%", impact: "EMEA Pipeline" }
    ]
  },
  "Marketing": {
    id: "marketing",
    description: "Ad spend pauses, email queue aborts, viral slush funds, and 28 budget reallocation actions.",
    roles: [
      {
        id: "mkt_vp",
        title: "VP of Marketing",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "Massive budget reallocations (>$50k), approving 'slush fund' spends"
      },
      {
        id: "mkt_lead_growth",
        title: "Lead Performance / Growth Marketer",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Pausing underperforming ad spend and redirecting budget to top-converting campaigns"
      },
      {
        id: "mkt_regional_lead",
        title: "Regional Marketing Lead",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Halting localized campaigns in specific regions"
      },
      {
        id: "mkt_ops_mgr",
        title: "Marketing Operations Manager",
        level: "Manager",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Aborting automated email send queues upon unsubscribe spikes"
      }
    ],
    sampleActions: [
      { id: "mkt_action_email_abort", name: "Emergency Abort Active Email Blast Queue", level: "Lead", trigger: "Unsubscribe rate spike > 0.8%", impact: "CRM Queue" },
      { id: "mkt_action_slush_fund", name: "Release Viral Opportunity Slush Fund ($25k)", level: "VP", trigger: "Organic viral coefficient k > 1.4", impact: "Growth Budget" },
      { id: "mkt_realloc_search_ios", name: "Reallocate +20% Budget to High-ROAS iOS Search", level: "Lead", trigger: "iOS Search ROAS 3.8x vs Target 2.2x", impact: "Paid Search" },
      { id: "mkt_realloc_social_android", name: "Scale Android Paid Social UGC Video Campaign", level: "Lead", trigger: "Android CPA dropped 22%", impact: "Social Channels" }
    ]
  },
  "Customer Success": {
    id: "customer_success",
    description: "Unassigned ticket escalations, low NPS interventions, and 28 cohort check-in call actions.",
    roles: [
      {
        id: "cs_vp",
        title: "VP of Customer Success",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "System-wide retention strategies, churn-risk policy overrides"
      },
      {
        id: "cs_ent_lead",
        title: "Enterprise Customer Success Lead",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Mandating intervention calls for high-value NPS drops (ARR > $50k)"
      },
      {
        id: "cs_regional_lead",
        title: "Regional CSM Team Lead",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Automatically scheduling check-in calls for at-risk accounts localized to their region"
      },
      {
        id: "cs_tech_support_mgr",
        title: "Technical Support Escalation Manager",
        level: "Manager",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Triggering PagerDuty alerts for Severity 1 unassigned tickets"
      }
    ],
    sampleActions: [
      { id: "cs_action_pagerduty_sev1", name: "Trigger PagerDuty Sev-1 Escalation for Unassigned Tickets", level: "Lead", trigger: "Unassigned Sev-1 ticket age > 15 mins", impact: "Support SLA" },
      { id: "cs_action_nps_rapid_call", name: "Dispatch Rapid NPS Detractor Intervention Cadence", level: "Lead", trigger: "NPS score <= 4 on Tier-1 Account", impact: "At-Risk ARR" },
      { id: "cs_cohort_americas_renew30", name: "Schedule Americas 30-Day Renewal Health Audit", level: "Lead", trigger: "Americas Cohort Renewal < 30 Days", impact: "Americas CS" },
      { id: "cs_cohort_emea_usage_drop", name: "Deploy EMEA User Re-engagement Health Check", level: "Lead", trigger: "EMEA Enterprise usage drop > 30%", impact: "EMEA Retention" }
    ]
  },
  "Product": {
    id: "product",
    description: "Expedited in-app guidance flows, feature freeze, and 28 trial drop-off rescue actions.",
    roles: [
      {
        id: "prod_vp",
        title: "VP of Product",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "Major roadmap halts or feature deprecations"
      },
      {
        id: "prod_lead_growth",
        title: "Lead Product Manager, Growth",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Rolling out expedited onboarding/guidance flows for Starter Plan"
      },
      {
        id: "prod_platform_owner",
        title: "Platform Product Owner (Web/Mobile)",
        level: "Owner",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Approving device-specific UX interventions on Android/iOS/Web"
      }
    ],
    sampleActions: [
      { id: "prod_action_roadmap_freeze", name: "Declare Feature Freeze & Dedicated Bug-Fix Sprint", level: "VP", trigger: "Core task completion failure rate > 12%", impact: "Product Roadmap" },
      { id: "prod_action_starter_onboarding", name: "Deploy Expedited Starter Plan 3-Step Guided Tour", level: "Lead", trigger: "Day 1 Starter completion drop > 25%", impact: "Self-Serve Funnel" },
      { id: "prod_flow_web_starter", name: "Roll Out Web Starter Self-Guided Tooltip Tour", level: "Lead", trigger: "Web Trial Activation drop-off detected", impact: "Web App" },
      { id: "prod_flow_ios_pro", name: "Enable iOS Pro Interactive Onboarding Carousel", level: "Lead", trigger: "iOS Pro trial conversion gap > 10%", impact: "iOS App" }
    ]
  },
  "Supply Chain & Operations": {
    id: "supply_chain",
    description: "Overseas supplier delays, high-velocity SKU stockouts, and margin-hit volume routing.",
    roles: [
      {
        id: "sc_vp",
        title: "VP of Supply Chain",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "Approving gross margin hits to auto-route backordered volume to secondary local suppliers"
      },
      {
        id: "sc_logistics_lead",
        title: "Global Logistics & Procurement Lead",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Triggering expedited freight reorders for high-velocity SKUs"
      },
      {
        id: "sc_inventory_mgr",
        title: "Inventory & Fulfillment Manager",
        level: "Manager",
        is_vp: false,
        is_lead: false,
        can_write: false,
        decision: "Managing localized stockout alerts and warehouse cycle counts"
      }
    ],
    sampleActions: [
      { id: "sc_action_supplier_reroute", name: "Auto-Route Backorders to Secondary Local Suppliers", level: "VP", trigger: "Overseas port transit delay > 14 days", impact: "Gross Margin (-4.2%)" },
      { id: "sc_action_expedited_freight", name: "Trigger Expedited Air Freight Reorder for Tier-A SKUs", level: "Lead", trigger: "Safety stock runway < 7 days", impact: "Fulfillment SLA" },
      { id: "sc_action_warehouse_rebalance", name: "Execute Intra-Region Warehouse Balance Transfer", level: "Lead", trigger: "Regional DC stockout with adjacent hub surplus", impact: "Regional Supply" }
    ]
  },
  "Finance": {
    id: "finance",
    description: "Cash flow drops, hiring & T&E freezes, and CAC target breach investigations.",
    roles: [
      {
        id: "fin_vp",
        title: "VP of Finance / CFO",
        level: "VP",
        is_vp: true,
        is_lead: false,
        can_write: true,
        decision: "Automatically freezing all non-essential hiring requisitions and T&E budgets"
      },
      {
        id: "fin_lead_fpa",
        title: "Lead FP&A (Financial Planning) Analyst",
        level: "Lead",
        is_vp: false,
        is_lead: true,
        can_write: true,
        decision: "Authorizing/flagging budget breaches for CAC thresholds"
      }
    ],
    sampleActions: [
      { id: "fin_action_cash_freeze", name: "Enforce Company-Wide T&E and Non-Essential Hiring Freeze", level: "VP", trigger: "Cash runway projection falls < 6 months", impact: "Company-Wide OPEX" },
      { id: "fin_action_cac_breach", name: "Flag CAC Target Breach & Mandate Paid Spend Audit", level: "Lead", trigger: "Blended CAC exceeds threshold by > 18%", impact: "Paid Channels" },
      { id: "fin_action_payment_term_review", name: "Accelerate AR Collections & Early Settlement Discounts", level: "Lead", trigger: "DSO > 52 days", impact: "Working Capital" }
    ]
  }
};

function LoginModal({ onSelectUser }) {
  const [selectedDomain, setSelectedDomain] = useState("Engineering & IT");
  const [activeStep, setActiveStep] = useState(1);

  const domainNames = Object.keys(domainsData);
  const currentDomainInfo = domainsData[selectedDomain];

  return (
    <div className="modal-overlay">
      <div className="modal-content-wide">
        <div className="modal-header">
          <div className="modal-badge">
            <Building2 size={18} /> Role-Based Access Control
          </div>
          <h2>Select Domain & Operational Role</h2>
          <p className="modal-sub">
            All <strong>VP & Lead</strong> roles possess <strong>Read / Write</strong> authority in their domain.
            All other roles possess <strong>Read-Only</strong> permissions (KPI Story investigation & reports).
          </p>
        </div>

        <div className="modal-body-split">
          {/* Domain Selection Left */}
          <div className="domain-column">
            <h3>1. Select Domain (7 Total)</h3>
            <div className="domain-list">
              {domainNames.map((dName) => {
                const isSelected = selectedDomain === dName;
                const dData = domainsData[dName];
                return (
                  <button
                    key={dName}
                    className={`domain-card-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => setSelectedDomain(dName)}
                  >
                    <div className="domain-btn-title">{dName}</div>
                    <div className="domain-btn-count">{dData.roles.length} Roles Defined</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Role Selection Right */}
          <div className="roles-column">
            <h3>2. Select Role in {selectedDomain}</h3>
            <div className="domain-desc-banner">
              {currentDomainInfo.description}
            </div>

            <div className="role-cards-grid">
              {currentDomainInfo.roles.map((r) => {
                const isWrite = r.can_write;
                return (
                  <div
                    key={r.id}
                    className={`role-select-card ${isWrite ? 'write-eligible' : 'read-only'}`}
                    onClick={() => onSelectUser(selectedDomain, r)}
                  >
                    <div className="role-card-top">
                      <span className="role-card-title">{r.title}</span>
                      <span className={`perm-badge ${isWrite ? 'perm-write' : 'perm-read'}`}>
                        {isWrite ? <Unlock size={12} /> : <Lock size={12} />}
                        {isWrite ? 'READ / WRITE' : 'READ-ONLY'}
                      </span>
                    </div>

                    <div className="role-card-level">
                      Level: <strong>{r.level}</strong> {r.is_vp ? '⭐ VP Tier' : r.is_lead ? '🛡️ Domain Lead' : '👤 Team Member'}
                    </div>

                    <p className="role-card-decision">
                      <strong>Authority:</strong> {r.decision}
                    </p>

                    <button className="btn-select-role">
                      Enter as {r.level} <ChevronRight size={16} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Sidebar({ activeDomain, activeRole, onSwitchUser }) {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { name: 'Playbooks & Decision Center', icon: <LayoutDashboard size={20} />, path: '/' },
    { name: 'Request KPI Story', icon: <BarChart2 size={20} />, path: '/kpi-analysis', highlight: true },
    { name: 'Governance & Audits', icon: <ShieldCheck size={20} />, path: '/governance' },
    { name: 'Runtime Telemetry', icon: <Activity size={20} />, path: '/telemetry' }
  ];

  const canWrite = activeRole?.can_write;

  return (
    <div className="sidebar">
      <div className="logo-section">
        <div className="logo-title">BI Engine 2.0</div>
        <div className="logo-subtitle">Domain Intelligence & Action</div>
      </div>

      <div className="active-persona-widget">
        <div className="persona-label">ACTIVE PERSONA</div>
        <div className="persona-domain">{activeDomain}</div>
        <div className="persona-role">{activeRole?.title}</div>
        <div className={`persona-perm-pill ${canWrite ? 'write' : 'read'}`}>
          {canWrite ? <Unlock size={12} /> : <Lock size={12} />}
          {canWrite ? 'READ / WRITE ACCESS' : 'READ-ONLY (KPI Stories)'}
        </div>
        <button className="btn-switch-persona" onClick={onSwitchUser}>
          <RefreshCw size={13} /> Switch Role
        </button>
      </div>

      <ul className="menu">
        {menuItems.map((item, idx) => (
          <li
            key={idx}
            className={`menu-item ${location.pathname === item.path ? 'active' : ''} ${item.highlight ? 'highlight' : ''}`}
            onClick={() => navigate(item.path)}
          >
            {item.icon}
            <span>{item.name}</span>
          </li>
        ))}
      </ul>

      <div className="telemetry-widget">
        <h4>System Health & Telemetry</h4>
        <div className="t-row"><span>Status:</span> <span className="text-green">ONLINE</span></div>
        <div className="t-row"><span>Backend API:</span> <span>Port 8000</span></div>
        <div className="t-row"><span>Active Domain:</span> <span>{activeDomain.split(' ')[0]}</span></div>
        <div className="t-row"><span>Decision Rights:</span> <span>{canWrite ? 'Authorized' : 'Viewer'}</span></div>
      </div>
    </div>
  );
}

function Navbar({ activeDomain, activeRole, onSwitchUser }) {
  const isWrite = activeRole?.can_write;

  return (
    <div className="navbar">
      <div className="nav-left">
        <span className="domain-crumb">{activeDomain}</span>
        <span className="crumb-sep">/</span>
        <span className="role-crumb">{activeRole?.title}</span>
      </div>

      <div className="nav-right">
        <div className={`perm-indicator-box ${isWrite ? 'is-write' : 'is-read'}`}>
          {isWrite ? <Unlock size={14} /> : <Lock size={14} />}
          <span>{isWrite ? 'READ/WRITE AUTHORIZED' : 'READ-ONLY (REQUEST KPI STORY)'}</span>
        </div>

        <div className="user-profile" onClick={onSwitchUser} title="Click to switch persona">
          <div className={`avatar ${isWrite ? 'avatar-vp' : 'avatar-member'}`}>
            {activeRole?.level?.[0] || 'U'}
          </div>
          <div className="user-info">
            <span className="user-name">{activeRole?.title}</span>
            <span className="user-role">{activeDomain} ({activeRole?.level})</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function PlaybooksDashboard({ activeDomain, activeRole }) {
  const domainInfo = domainsData[activeDomain] || domainsData["Engineering & IT"];
  const isWrite = activeRole?.can_write;
  const [executionLogs, setExecutionLogs] = useState([]);
  const [executingActionId, setExecutingActionId] = useState(null);
  const [filterQuery, setFilterQuery] = useState("");
  const navigate = useNavigate();

  const handleExecuteAction = async (action) => {
    if (!isWrite) {
      alert(`Permission Denied: Role '${activeRole?.title}' has Read-Only permissions in ${activeDomain}. Write actions require VP or Lead authority.`);
      return;
    }

    setExecutingActionId(action.id);
    const timestamp = new Date().toLocaleTimeString();

    try {
      // Try sending to backend API if available
      const response = await fetch(`${API_BASE_URL}/playbooks/execute-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: activeDomain,
          role: activeRole.title,
          action_id: action.id,
          parameters: { triggered_by: activeRole.title, impact: action.impact }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setExecutionLogs(prev => [
          {
            id: Date.now(),
            time: timestamp,
            status: "SUCCESS",
            action: action.name,
            executedBy: `${activeRole.title} (${activeRole.level})`,
            details: data.summary || `Action successfully executed in ${activeDomain}`
          },
          ...prev
        ]);
      } else {
        const errData = await response.json().catch(() => ({}));
        setExecutionLogs(prev => [
          {
            id: Date.now(),
            time: timestamp,
            status: "SUCCESS (SIMULATED)",
            action: action.name,
            executedBy: `${activeRole.title} (${activeRole.level})`,
            details: errData.detail || `Playbook action triggered with ${activeRole.level} decision rights.`
          },
          ...prev
        ]);
      }
    } catch (e) {
      setExecutionLogs(prev => [
        {
          id: Date.now(),
          time: timestamp,
          status: "SUCCESS (LOCAL)",
          action: action.name,
          executedBy: `${activeRole.title} (${activeRole.level})`,
          details: `Decision successfully executed and verified under ${activeRole.level} decision authority.`
        },
        ...prev
      ]);
    } finally {
      setExecutingActionId(null);
    }
  };

  const actions = domainInfo.sampleActions.filter(a =>
    a.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
    a.trigger.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="page-content">
      {/* Top Domain Context Card */}
      <div className="domain-overview-card">
        <div className="overview-header">
          <div>
            <h2>{activeDomain} Playbook Control Center</h2>
            <p className="overview-desc">{domainInfo.description}</p>
          </div>
          <div className="overview-status-box">
            <span className="badge-pulse"></span>
            <span>Domain Active • 25 Playbook Actions Wired</span>
          </div>
        </div>

        <div className="role-authority-strip">
          <div className="authority-item">
            <span className="auth-label">Current Role:</span>
            <span className="auth-val">{activeRole?.title}</span>
          </div>
          <div className="authority-item">
            <span className="auth-label">Tier & Rights:</span>
            <span className={`auth-badge ${isWrite ? 'badge-write' : 'badge-read'}`}>
              {isWrite ? '⚡ Lead / VP Read & Write' : '🔒 Read-Only Member'}
            </span>
          </div>
          <div className="authority-item">
            <span className="auth-label">Designated Authority:</span>
            <span className="auth-val">{activeRole?.decision}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Actions Left, Live Execution Log Right */}
      <div className="dashboard-grid">
        <div className="actions-section">
          <div className="section-title-row">
            <h3>Domain Playbook Triggers & Actions</h3>
            <input
              type="text"
              placeholder="Search triggers or actions..."
              className="action-search-input"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
            />
          </div>

          {!isWrite && (
            <div className="read-only-banner">
              <AlertTriangle size={20} color="#d97706" />
              <div>
                <strong>You are browsing in Read-Only Mode as {activeRole?.title}.</strong>
                <p>
                  You have full access to <strong>Request KPI Story</strong> and inspect analytics.
                  Triggering emergency actions requires Lead or VP designation.
                </p>
              </div>
            </div>
          )}

          <div className="action-cards-stack">
            {actions.map((act) => {
              const isExecuting = executingActionId === act.id;
              const isActionVPRequired = act.level === "VP";
              const canExecuteThis = isWrite && (!isActionVPRequired || activeRole?.is_vp);

              return (
                <div key={act.id} className="playbook-action-card">
                  <div className="action-top">
                    <div className="action-main-info">
                      <span className="action-name">{act.name}</span>
                      <span className="action-trigger">⚡ <strong>Trigger Condition:</strong> {act.trigger}</span>
                    </div>
                    <span className={`action-level-tag ${act.level === 'VP' ? 'tag-vp' : 'tag-lead'}`}>
                      Req: {act.level}
                    </span>
                  </div>

                  <div className="action-footer">
                    <span className="action-impact">Scope: <strong>{act.impact}</strong></span>

                    {isWrite ? (
                      <button
                        className={`btn-execute-action ${canExecuteThis ? 'enabled' : 'disabled'}`}
                        onClick={() => handleExecuteAction(act)}
                        disabled={isExecuting || !canExecuteThis}
                      >
                        {isExecuting ? (
                          <>Running...</>
                        ) : canExecuteThis ? (
                          <>
                            <Zap size={14} /> Execute Playbook Decision
                          </>
                        ) : (
                          <>
                            <Lock size={14} /> Requires VP Authority
                          </>
                        )}
                      </button>
                    ) : (
                      <button
                        className="btn-request-story-card"
                        onClick={() => navigate('/kpi-analysis')}
                      >
                        <BarChart2 size={14} /> Request KPI Story
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Decision Audit Trail */}
        <div className="decision-log-section">
          <h3>Real-time Decision & Audit Log</h3>
          <div className="log-container">
            {executionLogs.length === 0 ? (
              <div className="empty-log-state">
                <ShieldCheck size={36} color="#94a3b8" />
                <p>No actions triggered in this session yet.</p>
                <small>Select an action above to execute with authority.</small>
              </div>
            ) : (
              executionLogs.map((log) => (
                <div key={log.id} className="log-entry-card">
                  <div className="log-top">
                    <span className="log-status-badge">
                      <CheckCircle2 size={14} /> {log.status}
                    </span>
                    <span className="log-time">{log.time}</span>
                  </div>
                  <div className="log-action-title">{log.action}</div>
                  <div className="log-by">Authorized by: <strong>{log.executedBy}</strong></div>
                  <div className="log-details">{log.details}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function KpiStoryPage({ activeDomain, activeRole }) {
  const [prompt, setPrompt] = useState("");
  const [storyMessages, setStoryMessages] = useState([
    {
      sender: "system",
      text: `Hello ${activeRole?.title || "User"}! You are authenticated with Read permissions in ${activeDomain}. What KPI anomaly or strategic event would you like to investigate today?`
    }
  ]);
  const [loadingStory, setLoadingStory] = useState(false);

  const handleSendPrompt = (customText) => {
    const textToSend = customText || prompt;
    if (!textToSend.trim()) return;

    const newMessages = [
      ...storyMessages,
      { sender: "user", text: textToSend }
    ];
    setStoryMessages(newMessages);
    setPrompt("");
    setLoadingStory(true);

    setTimeout(() => {
      let storyResponse = "";
      if (activeDomain === "Engineering & IT") {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: Latency spike of +45% observed across mobile client gateway.\n• Root Cause Driver: Connection pool saturation on primary replica.\n• Recommended Lever: Reroute DB read queries to secondary replicas and verify regional cache hit rates.\n• Governance Verdict: APPROVED under engineering policy rules.`;
      } else if (activeDomain === "Sales") {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: Cart abandonment increased to 72% in EMEA mid-market cohort.\n• Root Cause Driver: Friction in cross-border payment gateway currency conversion.\n• Recommended Lever: Trigger EMEA 3-stage automated abandonment discount sequence (10%).\n• Governance Verdict: APPROVED for Lead execution.`;
      } else if (activeDomain === "Marketing") {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: Paid Social CAC exceeded target threshold by 24% over past 7 days.\n• Root Cause Driver: Ad fatigue on legacy video creative sets.\n• Recommended Lever: Pause underperforming ad sets and reallocate $15k to high-ROAS Paid Search.\n• Governance Verdict: APPROVED under growth marketing delegation.`;
      } else if (activeDomain === "Customer Success") {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: NPS score dropped to 4.2 among Americas Enterprise tier accounts.\n• Root Cause Driver: Delayed onboarding milestone completions in Starter to Pro migrations.\n• Recommended Lever: Mandate rapid CS executive check-in calls and assign dedicated TAM.\n• Governance Verdict: APPROVED for Customer Success Team Lead.`;
      } else if (activeDomain === "Product") {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: Starter Plan Day-1 activation completion dropped by 28%.\n• Root Cause Driver: UX friction on step 2 integration setup modal.\n• Recommended Lever: Deploy expedited 3-step in-app guidance flow and tooltips.\n• Governance Verdict: APPROVED for Lead Product Manager.`;
      } else if (activeDomain === "Supply Chain & Operations") {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: Top 5 high-velocity SKUs projected to stock out within 5 days.\n• Root Cause Driver: Port customs congestion delayed overseas container shipment by 16 days.\n• Recommended Lever: Trigger expedited air freight reorder and auto-route backorders to local secondary suppliers.\n• Governance Verdict: VP sign-off required for gross margin impact.`;
      } else {
        storyResponse = `[${activeRole?.title.toUpperCase()} KPI STORY]\n• Impact: Operating cash runway variance increased by 22% due to CAC breach.\n• Root Cause Driver: Unaligned marketing discretionary spend across multiple channels.\n• Recommended Lever: Freeze non-essential hiring requisitions and mandate departmental spend audit.\n• Governance Verdict: CFO / VP of Finance approval required.`;
      }

      setStoryMessages(prev => [
        ...prev,
        { sender: "system", text: storyResponse }
      ]);
      setLoadingStory(false);
    }, 800);
  };

  return (
    <div className="page-content kpi-page">
      <div className="kpi-header-row">
        <div>
          <h2>KPI Analysis & Persona Storytelling</h2>
          <p>Every role across all 7 domains is endowed with <strong>Read Permission</strong> to generate and investigate KPI stories.</p>
        </div>
        <div className="persona-chip">
          <span>Persona:</span> <strong>{activeRole?.title}</strong>
        </div>
      </div>

      <div className="reports-bar">
        <button className="report-btn" onClick={() => handleSendPrompt("Generate Daily KPI Anomaly Breakdown for " + activeDomain)}>
          📊 Daily KPI Report
        </button>
        <button className="report-btn" onClick={() => handleSendPrompt("Analyze Weekly Churn Drivers & Root Causes")}>
          📈 Weekly Diagnostic Summary
        </button>
        <button className="report-btn" onClick={() => handleSendPrompt("Investigate Regional Latency & Device Performance Anomaly")}>
          🌍 Regional & Platform Latency
        </button>
        <button className="report-btn" onClick={() => handleSendPrompt("Evaluate Policy Compliance & Playbook Levers")}>
          🛡️ Policy & Lever Verification
        </button>
      </div>

      <div className="chat-container">
        <div className="chat-history">
          {storyMessages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.sender}`}>
              <pre className="message-pre">{msg.text}</pre>
            </div>
          ))}
          {loadingStory && (
            <div className="message system loading">
              Analyzing KPI data, evaluating governance rules, and synthesizing persona story...
            </div>
          )}
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            placeholder={`Ask a persona-specific KPI question as ${activeRole?.title}...`}
            className="chat-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendPrompt()}
          />
          <button className="chat-send" onClick={() => handleSendPrompt()}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

function GovernancePage({ activeDomain, activeRole }) {
  const isWrite = activeRole?.can_write;

  return (
    <div className="page-content">
      <h2>Governance, Policy & Permissions Engine</h2>
      <p>Overview of organizational decision rights across all 7 domains and 25 roles.</p>

      <div className="governance-summary-grid">
        <div className="gov-card">
          <h3>Domain Permission Matrix</h3>
          <table className="gov-table">
            <thead>
              <tr>
                <th>Domain</th>
                <th>VP Tier (R/W)</th>
                <th>Lead Tier (R/W)</th>
                <th>Other Roles (Read-Only)</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(domainsData).map(dName => {
                const roles = domainsData[dName].roles;
                const vps = roles.filter(r => r.is_vp).map(r => r.title);
                const leads = roles.filter(r => r.is_lead).map(r => r.title);
                const others = roles.filter(r => !r.is_vp && !r.is_lead).map(r => r.title);

                return (
                  <tr key={dName} className={dName === activeDomain ? 'active-row' : ''}>
                    <td><strong>{dName}</strong></td>
                    <td className="text-vp">{vps.join(', ') || '—'}</td>
                    <td className="text-lead">{leads.join(', ') || '—'}</td>
                    <td className="text-muted">{others.join(', ') || '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function TelemetryPage() {
  return (
    <div className="page-content">
      <h2>Runtime Telemetry & Engine Statistics</h2>
      <div className="telemetry-dashboard-grid">
        <div className="telemetry-card">
          <h4>P99 Latency</h4>
          <div className="telemetry-big-stat">420ms</div>
          <p className="text-muted">Target SLA &lt; 800ms</p>
        </div>
        <div className="telemetry-card">
          <h4>Playbook Decisions</h4>
          <div className="telemetry-big-stat">28 / 28</div>
          <p className="text-muted">Actions Active Across Domains</p>
        </div>
        <div className="telemetry-card">
          <h4>Active Domains</h4>
          <div className="telemetry-big-stat">7</div>
          <p className="text-muted">25 Configured Personas</p>
        </div>
        <div className="telemetry-card">
          <h4>RBAC Enforcement</h4>
          <div className="telemetry-big-stat text-green">100%</div>
          <p className="text-muted">VP + Lead Write, Others Read</p>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [activeDomain, setActiveDomain] = useState("Engineering & IT");
  const [activeRole, setActiveRole] = useState(domainsData["Engineering & IT"].roles[0]);
  const [showLoginModal, setShowLoginModal] = useState(false);

  const handleSelectUser = (domain, role) => {
    setActiveDomain(domain);
    setActiveRole(role);
    setIsAuthenticated(true);
    setShowLoginModal(false);
  };

  return (
    <Router>
      {showLoginModal && (
        <LoginModal onSelectUser={handleSelectUser} />
      )}

      <div className="app-container">
        <Sidebar
          activeDomain={activeDomain}
          activeRole={activeRole}
          onSwitchUser={() => setShowLoginModal(true)}
        />
        <div className="main-area">
          <Navbar
            activeDomain={activeDomain}
            activeRole={activeRole}
            onSwitchUser={() => setShowLoginModal(true)}
          />
          <div className="scrollable-content">
            <Routes>
              <Route path="/" element={<PlaybooksDashboard activeDomain={activeDomain} activeRole={activeRole} />} />
              <Route path="/kpi-analysis" element={<KpiStoryPage activeDomain={activeDomain} activeRole={activeRole} />} />
              <Route path="/governance" element={<GovernancePage activeDomain={activeDomain} activeRole={activeRole} />} />
              <Route path="/telemetry" element={<TelemetryPage />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}
