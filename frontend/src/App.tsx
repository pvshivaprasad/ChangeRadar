import { useState } from 'react';
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Bell, BookOpen,
  Boxes, Braces, Check, ChevronDown, CircleHelp, Clock3, Command,
  GitBranch, GitCommitHorizontal, Github, LayoutDashboard, LifeBuoy,
  LockKeyhole, Menu, Plus, Radar, Search, Settings2, ShieldCheck,
  Sparkles, Workflow, X, Zap
} from 'lucide-react';

type Page = 'overview' | 'repositories' | 'analysis' | 'dependencies' | 'tests' | 'reports';

const navItems: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'repositories', label: 'Repositories', icon: Github },
  { id: 'analysis', label: 'Change analysis', icon: GitBranch },
  { id: 'dependencies', label: 'Dependency map', icon: Workflow },
  { id: 'tests', label: 'Test intelligence', icon: Check },
  { id: 'reports', label: 'Risk reports', icon: Activity },
];

function Brand({ light = false }: { light?: boolean }) {
  return <div className={`brand ${light ? 'brand-light' : ''}`}><span className="brand-mark"><Radar size={19} strokeWidth={2.2} /></span><span>change<span className="brand-strong">radar</span></span></div>;
}

function Landing({ onLaunch }: { onLaunch: () => void }) {
  return <div className="landing">
    <nav className="marketing-nav wrap">
      <Brand />
      <div className="marketing-links"><a href="#product">Product</a><a href="#how">How it works</a><a href="#principles">Principles</a></div>
      <button className="button button-dark button-small" onClick={onLaunch}>Open workspace <ArrowUpRight size={15}/></button>
    </nav>
    <main>
      <section className="hero wrap">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-dot"/> SOFTWARE CHANGE INTELLIGENCE</div>
          <h1>See the impact<br/>before it <em>happens.</em></h1>
          <p className="hero-lede">Every code change has a ripple effect. Understand dependencies, surface potential risks, and give your team the context to ship with confidence.</p>
          <div className="hero-actions"><button className="button button-lime" onClick={onLaunch}>Explore the workspace <ArrowRight size={17}/></button><a className="text-link" href="#how">See how it works <ArrowDownRight size={16}/></a></div>
          <div className="hero-proof"><div className="avatar-stack"><span>JD</span><span>MK</span><span>AS</span></div><span>Built for the people behind the code.</span></div>
        </div>
        <div className="hero-art" aria-label="Illustrative code dependency visualization">
          <div className="art-topline"><span>CHANGE GRAPH / 001</span><span className="live-indicator"><i/> LIVE SYSTEM VIEW</span></div>
          <div className="graph-canvas">
            <svg className="graph-lines" viewBox="0 0 560 430" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
              <path d="M280 211 L140 112 L66 220 M280 211 L424 105 L496 225 M280 211 L151 337 L67 275 M280 211 L417 337 L500 280 M140 112 L424 105 M151 337 L417 337" />
              <path className="graph-line-accent" d="M280 211 L424 105 L496 225 M280 211 L151 337" />
              <circle cx="280" cy="211" r="74" className="orbit orbit-one"/><circle cx="280" cy="211" r="111" className="orbit orbit-two"/>
            </svg>
            <div className="graph-node node-core"><span className="node-icon"><Braces size={20}/></span><b>auth.service</b><small>CORE MODULE</small></div>
            <div className="graph-node node-a"><span className="node-icon"><Boxes size={16}/></span><b>checkout</b></div>
            <div className="graph-node node-b"><span className="node-icon"><LockKeyhole size={16}/></span><b>sessions</b></div>
            <div className="graph-node node-c"><span className="node-icon"><Zap size={16}/></span><b>payments</b></div>
            <div className="graph-node node-d"><span className="node-icon"><GitBranch size={16}/></span><b>user.profile</b></div>
            <div className="graph-tag"><span/> 4 connected modules</div>
          </div>
          <div className="art-footer"><span>DEPENDENCY PREVIEW</span><span>Illustrative visualization</span></div>
        </div>
      </section>
      <section className="ticker"><div className="wrap ticker-inner"><span>BUILT FOR COMPLEX CODEBASES</span><span>DEPENDENCY AWARE</span><span>CHANGE CONTEXT</span><span>ENGINEERING CONFIDENCE</span></div></section>
      <section className="feature-section wrap" id="product">
        <div className="section-intro"><div className="eyebrow">A CLEARER VIEW OF CHANGE</div><h2>Less guesswork.<br/><em>Better engineering.</em></h2><p>ChangeRadar connects the dots between the code you touch and the systems that may depend on it.</p></div>
        <div className="feature-grid">
          <article className="feature-card feature-large"><div className="feature-icon"><Workflow size={21}/></div><div><span className="feature-index">01 / UNDERSTAND</span><h3>Map the connections.</h3><p>Explore how modules, functions and services relate to one another in a codebase.</p></div><div className="mini-map"><div className="mini-node mini-main">auth</div><div className="mini-node mini-one">session</div><div className="mini-node mini-two">checkout</div><div className="mini-node mini-three">profile</div><svg viewBox="0 0 360 120"><path d="M180 60 L70 25 M180 60 L290 25 M180 60 L180 105"/></svg></div></article>
          <article className="feature-card"><div className="feature-icon violet"><GitCommitHorizontal size={21}/></div><span className="feature-index">02 / TRACE</span><h3>Follow every change.</h3><p>Compare revisions and see which files, symbols and relationships changed.</p><div className="code-lines"><i/><i/><i/><i/><i/></div></article>
          <article className="feature-card"><div className="feature-icon amber"><ShieldCheck size={21}/></div><span className="feature-index">03 / ASSESS</span><h3>Surface what matters.</h3><p>Prioritize potential impact with evidence, context and clear explanations.</p><div className="risk-preview"><span><i/> Dependency path</span><span><i/> Test coverage gap</span><span><i/> API boundary</span></div></article>
        </div>
      </section>
      <section className="manifesto" id="how"><div className="wrap manifesto-inner"><div className="eyebrow">HOW IT WORKS</div><h2>From a code change<br/>to a clearer <em>decision.</em></h2><div className="steps"><div><b>01</b><h3>Connect</h3><p>Bring in a repository and let ChangeRadar build its code map.</p></div><div><b>02</b><h3>Compare</h3><p>Select a commit or pull request to understand what changed.</p></div><div><b>03</b><h3>Understand</h3><p>Review affected paths, suggested tests and evidence-backed findings.</p></div></div></div></section>
      <section className="closing wrap" id="principles"><div><div className="eyebrow">ENGINEERING, WITH CONTEXT</div><h2>Ship with your eyes<br/>wide <em>open.</em></h2></div><button className="button button-dark" onClick={onLaunch}>Explore ChangeRadar <ArrowUpRight size={17}/></button></section>
    </main>
    <footer className="marketing-footer wrap"><Brand/><span>© 2026 ChangeRadar. Built for thoughtful engineering.</span><span>PREVIEW / 0.1</span></footer>
  </div>;
}

function EmptyState({ title, description, action }: { title: string; description: string; action?: string }) {
  return <div className="empty-state"><div className="empty-icon"><Radar size={25}/></div><h3>{title}</h3><p>{description}</p>{action && <button className="button button-lime button-small">{action}<ArrowRight size={15}/></button>}</div>;
}

function Workspace({ onHome }: { onHome: () => void }) {
  const [page, setPage] = useState<Page>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showConnect, setShowConnect] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [notice, setNotice] = useState('');
  const active = navItems.find(item => item.id === page)!;
  const selectPage = (id: Page) => { setPage(id); setSidebarOpen(false); };
  const connect = () => { setNotice(repoUrl.trim() ? 'GitHub connection will be enabled in the next integration milestone.' : 'Enter a repository URL to continue.'); };
  return <div className="workspace-shell">
    {sidebarOpen && <button className="mobile-scrim" onClick={() => setSidebarOpen(false)} aria-label="Close navigation"/>}
    <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-head"><button className="brand-button" onClick={onHome}><Brand/></button><button className="icon-button mobile-close" onClick={() => setSidebarOpen(false)}><X size={18}/></button></div>
      <button className="workspace-switch"><span className="workspace-avatar">CR</span><span><b>Personal workspace</b><small>Free preview</small></span><ChevronDown size={15}/></button>
      <div className="nav-label">WORKSPACE</div>
      <nav className="side-nav">{navItems.map(item => { const Icon = item.icon; return <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => selectPage(item.id)}><Icon size={17}/><span>{item.label}</span>{item.id === 'analysis' && <span className="nav-new">NEW</span>}</button>; })}</nav>
      <div className="sidebar-bottom"><div className="sidebar-help"><div className="help-icon"><CircleHelp size={17}/></div><div><b>Need a hand?</b><small>Explore the product guide</small></div><ArrowUpRight size={14}/></div><button className="profile-button"><span className="profile-avatar">SP</span><span><b>Shiva Prasad</b><small>Workspace owner</small></span><Settings2 size={16}/></button></div>
    </aside>
    <main className="workspace-main">
      <header className="topbar"><div className="topbar-left"><button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)}><Menu size={19}/></button><span className="breadcrumb-muted">Workspace</span><span className="breadcrumb-slash">/</span><span>{active.label}</span></div><div className="topbar-right"><div className="search-shortcut"><Search size={15}/><span>Search</span><kbd>⌘ K</kbd></div><button className="icon-button" title="Notifications"><Bell size={17}/></button><span className="top-avatar">SP</span></div></header>
      <div className="page-content">
        <div className="page-heading"><div><div className="eyebrow">PERSONAL WORKSPACE <span className="heading-dot"/> PREVIEW</div><h1>{page === 'overview' ? 'Good to see you, Shiva.' : active.label}</h1><p>{page === 'overview' ? 'Your engineering picture, all in one place.' : page === 'repositories' ? 'Connect the codebases your team works on.' : page === 'analysis' ? 'Understand the potential impact of your next change.' : page === 'dependencies' ? 'Explore how the pieces of your codebase connect.' : page === 'tests' ? 'Find the tests that matter for each change.' : 'A history of your engineering risk assessments.'}</p></div>{page === 'repositories' && <button className="button button-lime button-small" onClick={() => setShowConnect(true)}><Plus size={16}/> Connect repository</button>}</div>
        {page === 'overview' && <>
          <div className="welcome-panel"><div className="welcome-copy"><span className="welcome-kicker"><Sparkles size={14}/> YOUR WORKSPACE IS READY</span><h2>Start with a<br/><em>repository.</em></h2><p>Connect a GitHub project to build its dependency map and run your first change impact analysis.</p><button className="button button-lime" onClick={() => setShowConnect(true)}>Connect a repository <ArrowRight size={16}/></button></div><div className="welcome-visual"><div className="welcome-orbit orbit-a"/><div className="welcome-orbit orbit-b"/><div className="welcome-core"><Radar size={37}/></div><div className="floating-chip chip-a"><GitBranch size={14}/> Source code</div><div className="floating-chip chip-b"><Workflow size={14}/> Dependencies</div><div className="floating-chip chip-c"><ShieldCheck size={14}/> Impact insights</div></div></div>
          <div className="metric-grid"><div className="metric-card"><div className="metric-top"><span>Repositories</span><Github size={16}/></div><strong>—</strong><small>Connect your first repository</small></div><div className="metric-card"><div className="metric-top"><span>Analyses run</span><Activity size={16}/></div><strong>—</strong><small>Waiting for your first analysis</small></div><div className="metric-card"><div className="metric-top"><span>Potential impacts</span><Workflow size={16}/></div><strong>—</strong><small>Will appear after analysis</small></div><div className="metric-card"><div className="metric-top"><span>Tests suggested</span><Check size={16}/></div><strong>—</strong><small>Insights from your codebase</small></div></div>
          <div className="lower-grid"><section className="surface-card recent-card"><div className="card-heading"><div><h3>Recent activity</h3><p>Your latest repository and analysis events</p></div><button className="quiet-button" onClick={() => selectPage('reports')}>View all <ArrowRight size={14}/></button></div><EmptyState title="Nothing here just yet" description="Your repository activity and analysis history will show up here once you get connected."/></section><section className="surface-card getting-card"><div className="card-heading"><div><h3>Getting started</h3><p>Your first steps with ChangeRadar</p></div><span className="progress-label">0 of 3</span></div><div className="checklist"><div><span className="step-number">01</span><span><b>Connect a repository</b><small>Bring in a GitHub codebase</small></span><ArrowRight size={15}/></div><div><span className="step-number">02</span><span><b>Build your code map</b><small>Discover modules and dependencies</small></span><ArrowRight size={15}/></div><div><span className="step-number">03</span><span><b>Run an impact analysis</b><small>Review your first change</small></span><ArrowRight size={15}/></div></div></section></div>
        </>}
        {page === 'repositories' && <section className="surface-card full-card"><div className="card-heading"><div><h3>Your repositories</h3><p>Repositories connected to this workspace</p></div><span className="subtle-count">0 repositories</span></div><EmptyState title="Your code belongs here" description="Connect a GitHub repository to scan its structure, map dependencies and start analysing changes." action="Connect GitHub repository"/></section>}
        {page === 'analysis' && <section className="surface-card full-card"><div className="card-heading"><div><h3>Change analysis</h3><p>Compare a base revision with a proposed change.</p></div><span className="status-pill"><i/> READY WHEN YOU ARE</span></div><EmptyState title="No repository selected" description="Connect a repository first. Then select a commit or pull request to generate an evidence-backed impact report." action="Go to repositories"/></section>}
        {page === 'dependencies' && <section className="surface-card full-card"><div className="card-heading"><div><h3>Dependency explorer</h3><p>Navigate module, class and function relationships.</p></div><span className="subtle-count">No graph generated</span></div><EmptyState title="Your code map starts here" description="Once a repository has been scanned, its dependency graph will become explorable here."/></section>}
        {page === 'tests' && <section className="surface-card full-card"><div className="card-heading"><div><h3>Test intelligence</h3><p>Prioritized test suggestions based on changed code paths.</p></div><span className="subtle-count">No recommendations</span></div><EmptyState title="No test insights yet" description="Run an impact analysis to discover relevant tests and potential coverage gaps."/></section>}
        {page === 'reports' && <section className="surface-card full-card"><div className="card-heading"><div><h3>Risk reports</h3><p>Review previous impact assessments and their evidence.</p></div><span className="subtle-count">0 reports</span></div><EmptyState title="Your reports will live here" description="Every completed analysis will create a traceable report linked to the repository revision."/></section>}
      </div>
      <footer className="workspace-footer"><span>CHANGE RADAR <b>PREVIEW 0.1</b></span><span><span className="footer-dot"/> All systems operational</span></footer>
    </main>
    {showConnect && <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) setShowConnect(false); }}><div className="connect-modal"><div className="modal-head"><div className="modal-icon"><Github size={21}/></div><button className="icon-button" onClick={() => setShowConnect(false)}><X size={18}/></button></div><span className="eyebrow">REPOSITORY INTEGRATION</span><h2>Bring your code<br/><em>into context.</em></h2><p>Connect a public GitHub repository to get started. Private repository authorization will be added with the GitHub App integration.</p><label htmlFor="repo-url">GitHub repository URL</label><input id="repo-url" value={repoUrl} onChange={e => { setRepoUrl(e.target.value); setNotice(''); }} placeholder="https://github.com/owner/repository"/><div className="modal-note"><LockKeyhole size={14}/> Read-only access is planned for the first integration.</div>{notice && <div className="inline-notice">{notice}</div>}<button className="button button-lime modal-submit" onClick={connect}>Continue <ArrowRight size={16}/></button><button className="modal-cancel" onClick={() => setShowConnect(false)}>Maybe later</button></div></div>}
  </div>;
}

export default function App() {
  const [inWorkspace, setInWorkspace] = useState(false);
  return inWorkspace ? <Workspace onHome={() => setInWorkspace(false)}/> : <Landing onLaunch={() => setInWorkspace(true)}/>;
}
