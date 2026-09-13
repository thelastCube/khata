import { useEffect, useState } from 'react'
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api } from './api'
import { Avatar, MonthContext, MonthPicker, thisMonth } from './components.jsx'
import Login from './pages/Login.jsx'
import Overview from './pages/Overview.jsx'
import AddExpense from './pages/AddExpense.jsx'
import FundDetail from './pages/FundDetail.jsx'
import Analysis from './pages/Analysis.jsx'
import Settings from './pages/Settings.jsx'
import Audit from './pages/Audit.jsx'
import Terms from './pages/Terms.jsx'

export const FONTS = {
  Fraunces: "'Fraunces', Georgia, serif",
  'JetBrains Mono': "'JetBrains Mono', ui-monospace, monospace",
  Merriweather: "'Merriweather', Georgia, serif",
}
const VARS = { display: '--font-display', body: '--font-body', mono: '--font-mono' }

export const ACCENTS = ['bee', 'ladybug', 'shark', 'caterpillar']
function initialAccent() { return localStorage.getItem('accent') || 'bee' }

function loadFonts() {
  return {
    display: localStorage.getItem('font_display') || 'Fraunces',
    body: localStorage.getItem('font_body') || 'Fraunces',
    mono: localStorage.getItem('font_mono') || 'JetBrains Mono',
  }
}

function initialTheme() {
  const saved = localStorage.getItem('theme')
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export default function App() {
  const [authed, setAuthed] = useState(null)
  const [profile, setProfile] = useState(null)
  const [month, setMonth] = useState(() => localStorage.getItem('month') || thisMonth())
  const [fonts, setFonts] = useState(loadFonts)
  const [theme, setTheme] = useState(initialTheme)
  const [accent, setAccent] = useState(initialAccent)

  const refreshProfile = () => api.whoami().then(setProfile).catch(() => {})

  useEffect(() => { localStorage.setItem('month', month) }, [month])
  useEffect(() => {
    for (const k of Object.keys(VARS)) {
      document.documentElement.style.setProperty(VARS[k], FONTS[fonts[k]] || FONTS.Fraunces)
      localStorage.setItem(`font_${k}`, fonts[k])
    }
  }, [fonts])
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])
  useEffect(() => {
    document.documentElement.setAttribute('data-accent', accent)
    localStorage.setItem('accent', accent)
  }, [accent])
  useEffect(() => {
    api.whoami().then((p) => { setProfile(p); setAuthed(true) }).catch(() => setAuthed(false))
  }, [])

  const setFont = (kind, name) => setFonts((f) => ({ ...f, [kind]: name }))

  if (authed === null) return <div className="app center muted" style={{ paddingTop: 80 }}>…</div>
  if (!authed) return <Login onDone={() => api.whoami().then((p) => { setProfile(p); setAuthed(true) })} />

  return (
    <MonthContext.Provider value={{ month, setMonth, fonts, setFont, FONTS, profile, refreshProfile, accent, setAccent, ACCENTS }}>
      <div className="app">
        <nav className="nav">
          <Link to="/terms" className="brand" title="what the words mean">khata</Link>
          <NavLink to="/" end>add</NavLink>
          <NavLink to="/overview">overview</NavLink>
          <NavLink to="/analysis">analyse</NavLink>
          <NavLink to="/settings">settings</NavLink>
          <NavLink to="/audit">log</NavLink>
          <span className="grow" />
          <MonthPicker />
          <button className="btn ghost small" title="toggle theme"
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
            {theme === 'dark' ? '☀' : '☾'}
          </button>
          {profile && (
            <Link to="/settings" title={`${profile.name} — settings`} className="row" style={{ textDecoration: 'none' }}>
              <Avatar value={profile.avatar} size={26} />
            </Link>
          )}
        </nav>
        <Routes>
          <Route path="/" element={<AddExpense />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/funds/:id" element={<FundDetail />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </MonthContext.Provider>
  )
}
