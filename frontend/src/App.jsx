import { useState, useRef, useEffect, useCallback } from 'react';
import './index.css';

/* Constants */
const API_URL      = 'http://localhost:8080/api/chat';
const SESSIONS_KEY = 'astroagent_sessions';
const ACTIVE_KEY   = 'astroagent_active';

const TOOL_LABELS = {
  geocode_place:       'Locating your birthplace',
  compute_birth_chart: 'Casting your natal chart',
  get_daily_transits:  "Reading today's skies",
  knowledge_lookup:    'Consulting the sacred texts',
};

const PLANET_MEANINGS = {
  Sun:     (s) => `Sun in ${s} illuminates your core identity — the soul's chosen path for this lifetime.`,
  Moon:    (s) => `Moon in ${s} governs your emotional inner world and instinctive reactions.`,
  Mercury: (s) => `Mercury in ${s} shapes how your mind works and how you communicate.`,
  Venus:   (s) => `Venus in ${s} reveals what you love, desire, and find beautiful.`,
  Mars:    (s) => `Mars in ${s} is your drive, ambition, and the fire that moves you to action.`,
  Jupiter: (s) => `Jupiter in ${s} marks where grace and expansion flow into your life.`,
  Saturn:  (s) => `Saturn in ${s} holds the lessons the cosmos placed in your path.`,
  Ascendant: (s) => `Ascendant in ${s} represents your outward mask and how you first approach the world.`,
};

const WELCOME = {
  id: 'welcome', role: 'agent', type: 'oracle',
  content: "Welcome, seeker.\n\nShare your birth details in the sidebar and I shall cast your natal chart from the real positions of the heavens. Ask me anything — your chart, today's transits, or what the cosmos holds for your path ahead.",
  timestamp: new Date().toISOString(),
};

/* Helpers */
const uid     = () => Math.random().toString(36).slice(2);
const fmt     = (d) => new Date(d).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
const fmtDate = (d) => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
const fmtShort= (d) => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

/* Session storage helpers */
function loadSessions() {
  try {
    const sessions = JSON.parse(localStorage.getItem(SESSIONS_KEY)) || [];
    sessions.forEach(s => {
      if (s.messages) {
        s.messages.forEach(m => {
          if (m.id === 'welcome' && typeof m.content === 'string' && m.content.includes("The stars have noted your arrival.")) {
            m.content = m.content.replace(" The stars have noted your arrival.", "");
          }
        });
      }
    });
    return sessions;
  } catch { return []; }
}
function saveSessions(s) {
  try { localStorage.setItem(SESSIONS_KEY, JSON.stringify(s)); } catch {}
}
function loadActiveId() { return localStorage.getItem(ACTIVE_KEY) || null; }
function saveActiveId(id) { localStorage.setItem(ACTIVE_KEY, id); }
function newSession() {
  return {
    id: uid(),
    title: 'New Reading',
    date: new Date().toISOString(),
    messages: [{ ...WELCOME, timestamp: new Date().toISOString() }],
    alignedUser: null,
  };
}

/* Small components */
function CopyBtn({ text }) {
  const [done, setDone] = useState(false);
  return (
    <button className="copy-btn" onClick={() => {
      navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1800);
    }}>{done ? 'Copied' : 'Copy'}</button>
  );
}

function PlanetBadge({ planet, sign }) {
  const [show, setShow] = useState(false);
  return (
    <div className="planet-badge"
      onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}      onBlur={() => setShow(false)} tabIndex={0}>
      {planet}: {sign}
      {show && <div className="badge-tooltip">{PLANET_MEANINGS[planet]?.(sign)}</div>}
    </div>
  );
}

function ToolCard({ tool }) {
  return (
    <div className="tool-indicator" role="status">
      <div className="tool-indicator-row">{TOOL_LABELS[tool] || tool}...</div>
      <div className="tool-progress"><div className="tool-progress-bar" /></div>
    </div>
  );
}

function Typing() {
  return (
    <div className="typing-indicator">
      <div className="dots"><div className="dot"/><div className="dot"/><div className="dot"/></div>
      <span>Processing request...</span>
    </div>
  );
}

/* Natal Console panel */
function NatalPanel({ chart, chartImage }) {
  if (!chart) return (
    <div className="natal-panel">
      <div className="natal-empty">
        Your natal chart has not been cast yet.<br />
        Enter your birth details in the sidebar and submit to generate your chart.
      </div>
    </div>
  );
  
  const pList = Object.entries(chart.planets || {});
  const houses = chart.houses || {};
  const aspects = chart.aspects || [];

  const handleDownload = () => {
    if (!chartImage) return;
    const link = document.createElement('a');
    link.download = `AstroAgent_Chart_${chart.birth_date}.svg`;
    link.href = chartImage;
    link.click();
  };

  const THEMES = {
    "1": "Identity & Appearance", "2": "Money & Values", "3": "Communication",
    "4": "Home & Roots", "5": "Creativity & Romance", "6": "Health & Service",
    "7": "Partnerships", "8": "Transformation & Secrets", "9": "Philosophy & Travel",
    "10": "Career & Reputation", "11": "Friendships & Goals", "12": "Spirituality & Subconscious"
  };

  const HOUSE_DESC = {
    "1": "This house represents your physical body, your approach to life, and the first impression you make. It is the core lens through which you interact with the world.",
    "2": "This house governs your personal finances, material possessions, and your core values. It reveals how you build security and self-worth.",
    "3": "This house rules communication, learning, siblings, and your immediate environment. It dictates your mental habits and how you process information.",
    "4": "The foundation of your chart. It represents home, family, roots, and your deepest emotional security. It is your private sanctuary.",
    "5": "This house governs creativity, romance, playfulness, and children. It shows how you express joy, take risks, and find pleasure.",
    "6": "This house rules daily routines, health, work environments, and acts of service. It reveals your habits and how you maintain wellness.",
    "7": "The house of partnerships, marriage, and close relationships. It shows what you seek in a significant other and how you collaborate.",
    "8": "This house governs transformation, shared resources, intimacy, and profound psychological depths. It is the realm of death, rebirth, and mystery.",
    "9": "This house represents higher learning, philosophy, travel, and the search for meaning. It reveals your belief systems and desire for expansion.",
    "10": "The highest point of your chart. It rules your career, public reputation, and long-term achievements. It shows your legacy to the world.",
    "11": "This house governs friendships, community, social networks, and your greatest hopes. It shows how you fit into the collective.",
    "12": "The house of the subconscious, spirituality, hidden strengths, and isolation. It reveals karmic patterns and where you connect to the divine."
  };

  return (
    <div className="natal-panel">
      <h2 style={{ marginBottom: '0.5rem' }}>Your Celestial Map</h2>
      <p className="subtitle" style={{ marginBottom: '2rem' }}>Whole Sign Houses</p>

      {chartImage && (
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <img src={chartImage} alt="Birth Chart Wheel" style={{ maxWidth: '100%', height: 'auto', borderRadius: '50%', boxShadow: '0 0 40px rgba(230, 213, 184, 0.1)' }} />
          <div style={{ marginTop: '1rem' }}>
            <button className="btn-align" onClick={handleDownload} style={{ width: 'auto', padding: '0.5rem 1.5rem', fontSize: '0.9rem' }}>Download Chart</button>
          </div>
        </div>
      )}

      <h2 style={{ marginTop: '3rem' }}>Planetary Positions</h2>
      <table className="natal-table">
        <thead>
          <tr><th>Planet</th><th>Sign</th><th>Degree</th><th>House</th></tr>
        </thead>
        <tbody>
          {pList.map(([p, data]) => (
            <tr key={p}>
              <td style={{ fontWeight: 600, color: 'var(--warm-brown)' }}>{p}</td>
              <td className="sign-cell">{data.sign}</td>
              <td className="deg-cell">{Math.floor(data.degrees % 30)}° {Math.round((data.degrees % 1) * 60)}'</td>
              <td style={{ fontSize: '0.85rem' }}>{data.house}{data.house === 1 ? 'st' : data.house === 2 ? 'nd' : data.house === 3 ? 'rd' : 'th'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ marginTop: '3rem' }}>The 12 Houses</h2>
      <table className="natal-table">
        <thead>
          <tr><th>House</th><th>Sign on Cusp</th><th>Planets Residing</th><th>Key Theme</th></tr>
        </thead>
        <tbody>
          {Object.entries(houses).map(([hNum, hData]) => {
            const inHouse = pList.filter(([_, pd]) => String(pd.house) === String(hNum)).map(x => x[0]).join(', ') || '—';
            return (
              <tr key={hNum}>
                <td style={{ fontWeight: 600, color: 'var(--warm-brown)' }}>{hNum}{hNum === '1' ? 'st' : hNum === '2' ? 'nd' : hNum === '3' ? 'rd' : 'th'}</td>
                <td className="sign-cell">{hData.sign}</td>
                <td>{inHouse}</td>
                <td style={{ fontSize: '0.85rem' }}>{THEMES[hNum]}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h2 style={{ marginTop: '3rem' }}>House Explanations</h2>
      <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
        {Object.entries(houses).map(([hNum, hData]) => {
          const inHouse = pList.filter(([_, pd]) => String(pd.house) === String(hNum)).map(x => x[0]);
          const theme = THEMES[hNum];
          return (
            <div key={hNum} style={{ padding: '1.25rem', background: 'var(--panel)', borderRadius: '12px', border: '1px solid var(--border-gold)' }}>
              <h3 style={{ color: 'var(--saffron)', marginBottom: '0.6rem', fontSize: '1.05rem', letterSpacing: '0.02em' }}>
                {hNum}{hNum === '1' ? 'st' : hNum === '2' ? 'nd' : hNum === '3' ? 'rd' : 'th'} House — {theme}
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--deep-brown)', lineHeight: '1.6', marginBottom: '0.75rem', fontStyle: 'italic', opacity: 0.9 }}>
                {HOUSE_DESC[hNum]}
              </p>
              <p style={{ fontSize: '0.88rem', color: 'var(--deep-brown)', lineHeight: '1.6' }}>
                Ruled by <strong>{hData.sign}</strong>, this area of your life is infused with the natural energy of {hData.sign}. 
                {inHouse.length > 0 
                  ? ` The presence of ${inHouse.join(' and ')} brings an active planetary influence here, intensely highlighting these themes in your life journey.` 
                  : ` With no planets currently residing here, these matters flow naturally without intense karmic friction, guided quietly by ${hData.sign}.`}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}



/* Sidebar */
function Sidebar({ onAlign, onNewReading, onLoadSession, onDeleteSession,
  westernChart, vedicChart, sessions, activeId, isOpen, onClose }) {

  const [form, setForm]     = useState({ name: '', gender: '', date: '', hour: '12', min: '00', ampm: 'AM', place: '' });
  const [errors, setErrors] = useState({});
  const [sugg, setSugg]     = useState([]);
  const [aligned, setAligned] = useState(false);
  const [mode, setMode]     = useState('western');
  const [showHistory, setShowHistory] = useState(true);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const validate = () => {
    const e = {};
    if (!form.date) {
      e.date = 'Required';
    } else {
      const year = parseInt(form.date.split('-')[0]);
      if (year < 1900 || year > 2100) {
        e.date = 'Invalid Year (must be 1900-2100)';
      }
    }
    if (!form.hour || !form.min) e.time = 'Required';
    if (!form.place.trim()) e.place = 'Required';
    if (!form.gender) e.gender = 'Required';
    setErrors(e);
    return !Object.keys(e).length;
  };

  const handleAlign = () => {
    if (!validate()) return;
    setSugg([]);
    setAligned(true);
    let hr = parseInt(form.hour);
    if (form.ampm === 'PM' && hr < 12) hr += 12;
    if (form.ampm === 'AM' && hr === 12) hr = 0;
    const time24 = `${hr.toString().padStart(2, '0')}:${form.min}`;
    onAlign({ ...form, time: time24 }, mode);
    setTimeout(() => setAligned(false), 3000);
  };

  const chart = mode === 'western' ? westernChart : vedicChart;
  const allFilled = form.date && form.hour && form.min && form.place.trim() && form.gender;

  return (
    <>
      <div className={`sidebar-overlay${isOpen ? ' open' : ''}`} onClick={onClose} aria-hidden />
      <aside className={`sidebar${isOpen ? ' open' : ''}`} aria-label="Sidebar">

        <div className="sidebar-logo">
          <h1>AstroAgent</h1>
          <span>ज्योतिष — Aradhana Companion</span>
        </div>

        <div className="sidebar-section-title">Birth Details</div>
        <p style={{ fontSize: '0.75rem', color: 'var(--muted-brown)', marginBottom: '0.9rem', lineHeight: 1.6 }}>
          Configure your celestial coordinates.
        </p>

        <div className="mode-toggle" role="group" aria-label="Zodiac system">
          {['western', 'vedic'].map(m => (
            <button key={m} className={`mode-btn${mode === m ? ' active' : ''}`} onClick={() => setMode(m)}>
              {m === 'western' ? 'Western' : 'Vedic'}
            </button>
          ))}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input id="name" className="field" type="text" placeholder="Your name"
              value={form.name} onChange={e => set('name', e.target.value)} />
          </div>
          <div className="form-group">
            <label htmlFor="gender">Gender</label>
            <select id="gender" className={`field${errors.gender ? ' error-field' : ''}`}
              value={form.gender} onChange={e => { set('gender', e.target.value); setErrors(er => ({ ...er, gender: '' })); }}>
              <option value="">Select</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </select>
            {errors.gender && <span className="field-error">{errors.gender}</span>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="dob">Date of Birth</label>
          <input id="dob" className={`field${errors.date ? ' error-field' : ''}`} type="date"
            value={form.date} onChange={e => { set('date', e.target.value); setErrors(er => ({ ...er, date: '' })); }} />
          {errors.date && <span className="field-error">{errors.date}</span>}
        </div>

        <div className="form-group">
          <label>Time of Birth (AM/PM)</label>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            <select className={`field${errors.time ? ' error-field' : ''}`} style={{ flex: 1, padding: '0.5rem' }}
              value={form.hour} onChange={e => { set('hour', e.target.value); setErrors(er => ({ ...er, time: '' })); }}>
              {Array.from({ length: 12 }, (_, i) => {
                const h = (i + 1).toString().padStart(2, '0');
                return <option key={h} value={h}>{h}</option>;
              })}
            </select>
            <span style={{ display: 'flex', alignItems: 'center', color: 'var(--muted-brown)' }}>:</span>
            <select className={`field${errors.time ? ' error-field' : ''}`} style={{ flex: 1, padding: '0.5rem' }}
              value={form.min} onChange={e => { set('min', e.target.value); setErrors(er => ({ ...er, time: '' })); }}>
              {Array.from({ length: 60 }, (_, i) => {
                const m = i.toString().padStart(2, '0');
                return <option key={m} value={m}>{m}</option>;
              })}
            </select>
            <select className="field" style={{ flex: 1, padding: '0.5rem' }}
              value={form.ampm} onChange={e => set('ampm', e.target.value)}>
              <option value="AM">AM</option>
              <option value="PM">PM</option>
            </select>
          </div>
          {errors.time && <span className="field-error">{errors.time}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="place">Place of Birth</label>
          <div className="autocomplete-wrapper">
            <input id="place" className={`field${errors.place ? ' error-field' : ''}`}
              type="text" placeholder="City, Country" value={form.place} autoComplete="off"
              onChange={e => {
                set('place', e.target.value);
                setErrors(er => ({ ...er, place: '' }));
                setSugg(e.target.value.length > 2
                  ? [e.target.value + ', India', e.target.value + ', USA', e.target.value + ', UK']
                  : []);
              }} />
            {sugg.length > 0 && (
              <ul className="autocomplete-list" role="listbox">
                {sugg.map(s => (
                  <li key={s} className="autocomplete-item" role="option"
                    onClick={() => { set('place', s); setSugg([]); }}>{s}</li>
                ))}
              </ul>
            )}
          </div>
          {errors.place && <span className="field-error">{errors.place}</span>}
        </div>

        <button className="btn-align" onClick={handleAlign} disabled={!allFilled}>
          Generate Birth Chart
        </button>

        {aligned && <div className="chart-success" role="status">Your birth chart is ready</div>}

        {chart && (
          <div className="planet-summary">
            <div className="sidebar-section-title" style={{ marginBottom: '0.6rem' }}>Natal Console</div>
            <div className="planet-grid">
              {Object.entries(chart).slice(0, 5).map(([planet, d]) => (
                <div className="planet-row" key={planet}>
                  <span className="planet-name">{planet}</span>
                  <span className="planet-sign">{d.sign}</span>
                  <span className="planet-deg">{d.degrees}°</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Past Readings */}
        <div className="history-section">
          <div className="sidebar-section-title" style={{ cursor: 'pointer', userSelect: 'none' }}
            onClick={() => setShowHistory(h => !h)}>
            Past Readings {showHistory ? '▾' : '▸'}
          </div>
          {showHistory && (
            <>
              <div className="history-list">
                {sessions.length === 0 && (
                  <p style={{ fontSize: '0.72rem', color: 'var(--muted-brown)', fontStyle: 'italic', padding: '0.3rem 0' }}>
                    No past readings yet.
                  </p>
                )}
                {[...sessions].reverse().map(s => (
                  <button key={s.id}
                    className={`history-item${s.id === activeId ? ' active' : ''}`}
                    onClick={() => { onLoadSession(s.id); onClose(); }}
                    title={s.title}>
                    <div className="history-item-text">
                      <div className="history-item-title">{s.title}</div>
                      <div className="history-item-date">
                        {fmtShort(s.date)} · {Math.max(0, s.messages.length - 1)} messages
                      </div>
                    </div>
                    <button className="history-item-del" title="Delete"
                      onClick={e => { e.stopPropagation(); onDeleteSession(s.id); }}
                      aria-label="Delete session">✕</button>
                  </button>
                ))}
              </div>
              <button className="btn-new-reading" onClick={() => { onNewReading(); onClose(); }}>
                + New Reading
              </button>
            </>
          )}
        </div>

        <div className="sidebar-footer">AstroAgent</div>
      </aside>
    </>
  );
}

/* App */
export default function App() {
  const initState = () => {
    const sessions = loadSessions();
    const activeId = loadActiveId();
    const active   = sessions.find(s => s.id === activeId) || sessions[0];
    if (active) return { sessions, activeId: active.id, messages: active.messages, alignedUser: active.alignedUser || null };
    const first = newSession();
    saveSessions([first]);
    saveActiveId(first.id);
    return { sessions: [first], activeId: first.id, messages: first.messages, alignedUser: null };
  };

  const init = initState();
  const [sessions, setSessions]     = useState(init.sessions);
  const [activeId, setActiveId]     = useState(init.activeId);
  const [messages, setMessages]     = useState(init.messages);
  const [input, setInput]           = useState('');
  const [loading, setLoading]       = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const [streamId, setStreamId]     = useState(null);
  const [westernChart, setWestern]  = useState(null);
  const [vedicChart, setVedic]      = useState(null);
  const [chartImage, setChartImage] = useState(null);
  const [badges, setBadges]         = useState([]);
  const [sidebarOpen, setSidebar]   = useState(false);
  const [showScroll, setShowScroll] = useState(false);
  const [activeTab, setTab]         = useState('chat');
  const [sessionDate]               = useState(new Date());
  const [currentMode, setMode]      = useState('western');
  const [alignedUser, setAlignedUser] = useState(init.alignedUser);

  const scrollRef = useRef(null);
  const inputRef  = useRef(null);
  const abort     = useRef(null);

  // Persist on every message change
  useEffect(() => {
    setSessions(prev => {
      const updated = prev.map(s => {
        if (s.id !== activeId) return s;
        const firstUser = messages.find(m => m.role === 'user');
        const title = firstUser
          ? firstUser.content.slice(0, 36) + (firstUser.content.length > 36 ? '…' : '')
          : 'New Reading';
        return { ...s, messages, title, alignedUser };
      });
      saveSessions(updated);
      return updated;
    });
  }, [messages, activeId, alignedUser]);

  const scrollBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, []);
  useEffect(() => { scrollBottom(); }, [messages, loading, activeTool]);

  const handleLoadSession = (id) => {
    const s = sessions.find(s => s.id === id);
    if (!s) return;
    setActiveId(id); saveActiveId(id);
    setMessages(s.messages);
    setAlignedUser(s.alignedUser || null);
    setWestern(null); setVedic(null); setChartImage(null); setBadges([]);
  };

  const handleNewReading = () => {
    const s = newSession();
    const updated = [...sessions, s];
    saveSessions(updated); setSessions(updated);
    setActiveId(s.id); saveActiveId(s.id);
    setMessages(s.messages);
    setAlignedUser(null);
    setWestern(null); setVedic(null); setChartImage(null); setBadges([]);
  };

  const handleDeleteSession = (id) => {
    const updated = sessions.filter(s => s.id !== id);
    saveSessions(updated); setSessions(updated);
    if (id === activeId) {
      if (updated.length) handleLoadSession(updated[updated.length - 1].id);
      else handleNewReading();
    }
  };

  const send = async (text, mode) => {
    const userMsg = { id: uid(), role: 'user', content: text, timestamp: new Date().toISOString() };
    const agentId = uid();
    const historyPayload = messages.slice(-4).map(m => ({ role: m.role, content: m.content }));
    setMessages(prev => [...prev, userMsg, {
      id: agentId, role: 'agent', type: 'insight',
      content: '', tools: [], timestamp: new Date().toISOString()
    }]);
    setInput(''); setLoading(true); setActiveTool(null);

    try {
      abort.current?.abort();
      abort.current = new AbortController();
      const currentChart = (mode || currentMode) === 'vedic' ? vedicChart : westernChart;
      const ctx = alignedUser ? { ...alignedUser, computed_chart: currentChart } : null;

      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, mode: mode || currentMode, user_context: ctx, history: historyPayload }),
        signal: abort.current.signal,
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const dec = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = dec.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ') || line === 'data: [DONE]') continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token') {
              setLoading(false); setActiveTool(null); setStreamId(agentId);
              setMessages(prev => prev.map(m =>
                m.id === agentId ? { ...m, content: m.content + data.content } : m
              ));
            } else if (data.type === 'tool_start') {
              setActiveTool(data.tool); setLoading(false);
              setMessages(prev => prev.map(m =>
                m.id === agentId ? { ...m, tools: [...(m.tools || []), { name: data.tool, status: 'running', startedAt: data.started_at }] } : m
              ));
            } else if (data.type === 'tool_end') {
              setActiveTool(null);
              setMessages(prev => prev.map(m =>
                m.id === agentId ? {
                  ...m,
                  tools: (m.tools || []).map(t => t.name === data.tool ? { ...t, status: 'complete', completedAt: data.completed_at, durationMs: data.duration_ms } : t)
                } : m
              ));
              if (data.tool === 'compute_birth_chart') {
                try {
                  const raw = JSON.parse(data.output);
                  if (raw?.planets) {
                    if ((mode || currentMode) === 'vedic') setVedic(raw);
                    else setWestern(raw);
                    setBadges([
                      { planet: 'Sun', sign: raw.planets['Sun']?.sign },
                      { planet: 'Moon', sign: raw.planets['Moon']?.sign },
                      { planet: 'Ascendant', sign: raw.ascendant?.sign }
                    ].filter(b => b.sign));

                    const user = alignedUser || { name: 'Seeker', date: raw.birth_date, time: raw.birth_time, place: 'Unknown' };
                    fetch(API_URL.replace('/api/chat', '/api/chart/image'), {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        planets: raw.planets,
                        houses: raw.houses || {},
                        ascendant: raw.ascendant?.degrees || 0,
                        midheaven: raw.midheaven?.degrees || 0,
                        name: user.name || 'Seeker',
                        birth_info: `${user.date} | ${user.time} | ${user.place}`
                      })
                    }).then(r => r.json()).then(res => {
                       if (res.success) setChartImage(res.image_base64);
                    }).catch(() => {});
                  }
                } catch {}
              }
            } else if (data.type === 'error') {
              setMessages(prev => [...prev, {
                id: uid(), role: 'error',
                content: 'The cosmos are quiet right now. Please try again in a moment.',
                timestamp: new Date().toISOString()
              }]);
            }
          } catch {}
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages(prev => [...prev, {
          id: uid(), role: 'error',
          content: 'The cosmos are quiet right now. Please ensure the backend server is running.',
          timestamp: new Date().toISOString()
        }]);
      }
    } finally {
      setLoading(false); setActiveTool(null); setStreamId(null);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    send(input.trim());
  };

  const handleAlign = (form, mode) => {
    setMode(mode);
    setAlignedUser(form);
    const system = mode === 'vedic' ? 'Vedic (Sidereal/Lahiri)' : 'Western (Tropical)';
    const msg = `${form.name ? `My name is ${form.name}. I was` : 'I was'} born on ${form.date} at ${form.time} in ${form.place}. Please cast my birth chart using the ${system} system.`;
    send(msg, mode);
    setSidebar(false);
  };

  return (
    <div className="layout">
      <Sidebar
        onAlign={handleAlign}
        onNewReading={handleNewReading}
        onLoadSession={handleLoadSession}
        onDeleteSession={handleDeleteSession}
        westernChart={westernChart}
        vedicChart={vedicChart}
        sessions={sessions}
        activeId={activeId}
        isOpen={sidebarOpen}
        onClose={() => setSidebar(false)}
      />

      <main className="chat-main">
        <header className="top-bar">
          <div className="top-bar-left">
            <button className="btn-menu" onClick={() => setSidebar(o => !o)}>☰ Menu</button>
            <div className="tab-strip">
              {[['chat', 'Chat'], ['natal', 'Birth Chart']].map(([key, label]) => (
                <button key={key} className={`tab${activeTab === key ? ' active' : ''}`} onClick={() => setTab(key)}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          {badges.length > 0 && (
            <div className="badge-strip">
              {badges.map(b => <PlanetBadge key={b.planet} planet={b.planet} sign={b.sign} />)}
            </div>
          )}
          <span className="session-info">{fmtDate(sessionDate)}</span>
        </header>

        {activeTab === 'natal' ? (
          <NatalPanel chart={westernChart || vedicChart} chartImage={chartImage} />
        ) : activeTab === 'numerology' ? (
          <NumerologyPanel user={alignedUser} />
        ) : (
          <>
            <section className="messages" ref={scrollRef}
              onScroll={() => {
                const el = scrollRef.current;
                if (el) setShowScroll(el.scrollHeight - el.scrollTop - el.clientHeight > 120);
              }}>
              <div className="time-divider">{fmtDate(sessionDate)}</div>

              {messages.map(msg => {
                if (msg.role === 'agent') return (
                  <div key={msg.id} className="msg-agent">
                    <div className="msg-agent-bubble">
                      {msg.tools && msg.tools.length > 0 && (
                        <div className="workflow-dashboard">
                          <div className="workflow-header"> TOOL ACTIVITY</div>
                          <div className="workflow-steps">
                            {msg.tools.map((t, i) => (
                              <div key={i} className={`workflow-step ${t.status}`}>
                                <div className="workflow-step-icon">
                                  {t.status === 'running' ? '⏳' : t.status === 'complete' ? '✓' : '❌'}
                                </div>
                                <div className="workflow-step-content">
                                  <div className="workflow-step-title">
                                    <span className="step-num">Step {i + 1}</span>
                                    <span className="step-label">{TOOL_LABELS[t.name] || t.name}</span>
                                  </div>
                                  <div className="workflow-technical-label">{t.name}()</div>
                                  {t.status === 'complete' && t.durationMs !== undefined && (
                                    <div className="workflow-timing">Completed in {(t.durationMs / 1000).toFixed(2)}s</div>
                                  )}
                                  {t.status === 'running' && (
                                    <div className="workflow-timing">Running...</div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="workflow-footer">
                            <div className="footer-stat">
                              <span className="stat-value">{msg.tools.length}</span>
                              <span className="stat-label">Tool{msg.tools.length > 1 ? 's' : ''} Executed</span>
                            </div>
                            <div className="footer-stat">
                              <span className="stat-label">Total Time:</span>
                              <span className="stat-value">{(msg.tools.reduce((acc, t) => acc + (t.durationMs || 0), 0) / 1000).toFixed(2)}s</span>
                            </div>
                            <div className="footer-stat">
                              <span className="stat-label">Status:</span>
                              <span className={`stat-value ${msg.tools.some(t => t.status === 'failed') ? 'error' : msg.tools.some(t => t.status === 'running') ? 'running' : 'success'}`}>
                                {msg.tools.some(t => t.status === 'failed') ? 'Failed' : msg.tools.some(t => t.status === 'running') ? 'In Progress' : 'Success'}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                      <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                      {msg.id === streamId && <span className="cursor" />}
                      {msg.id !== streamId && msg.content && <CopyBtn text={msg.content} />}
                    </div>
                    <div className="msg-timestamp">{fmt(msg.timestamp)}</div>
                  </div>
                );
                if (msg.role === 'user') return (
                  <div key={msg.id} className="msg-user">
                    <div className="msg-user-bubble">{msg.content}</div>
                    <div className="msg-user-timestamp">{fmt(msg.timestamp)}</div>
                  </div>
                );
                if (msg.role === 'error') return (
                  <div key={msg.id} className="msg-error">{msg.content}</div>
                );
                return null;
              })}

              {loading && !activeTool && <Typing />}
              {activeTool && <ToolCard tool={activeTool} />}
            </section>

            {showScroll && (
              <button className="scroll-pill" onClick={scrollBottom}>Scroll to latest</button>
            )}

            <footer className="input-area">
              <form className="input-row" onSubmit={handleSubmit}>
                <input ref={inputRef} className="chat-input" type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) handleSubmit(e); }}
                  placeholder="Type your message..."
                  disabled={loading && !activeTool}
                  maxLength={500}
                  aria-label="Message input"
                />
                <button type="submit" className="btn-send" disabled={!input.trim() || loading}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                </button>
              </form>
              <div className="input-footer">
                <span className="input-disclaimer">For spiritual guidance only. Not medical or financial advice.</span>
                <span className="char-count">{input.length}/500</span>
              </div>
              <div className="wisdom-footer">Wisdom is Eternal</div>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}
