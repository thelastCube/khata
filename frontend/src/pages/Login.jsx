import { useEffect, useState } from 'react'
import { api } from '../api'
import { Avatar } from '../components.jsx'

export default function Login({ onDone }) {
  const [profiles, setProfiles] = useState([])
  const [sel, setSel] = useState(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { api.profiles().then(setProfiles).catch((e) => setError(e.message)) }, [])

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await api.login(sel.id, password)
      onDone()
    } catch (err) {
      setError(err.message); setBusy(false)
    }
  }

  return (
    <div className="app center" style={{ paddingTop: 72, maxWidth: sel ? 440 : 620 }}>
      <h1 style={{ marginBottom: 8 }}>khata</h1>
      <p className="muted" style={{ marginTop: 0 }}>a cozy place for your money</p>

      {!sel ? (
        <div>
          <div className="muted" style={{ margin: '18px 0 20px' }}>who's this?</div>
          <div className="profile-tiles">
            {profiles.map((p) => (
              <button key={p.id} className="profile-tile" onClick={() => { setSel(p); setError('') }}>
                <Avatar value={p.avatar} size={104} />
                <span>{p.name}</span>
              </button>
            ))}
          </div>
          {profiles.length === 0 && <div className="muted center">No profiles found.</div>}
          {error && <div className="error">{error}</div>}
        </div>
      ) : (
        <form onSubmit={submit} className="card stack">
          <div className="row" style={{ gap: 12, justifyContent: 'center', marginBottom: 4 }}>
            <Avatar value={sel.avatar} size={48} />
            <b style={{ fontSize: '1.2rem' }}>{sel.name}</b>
          </div>
          <input type="password" placeholder="password" autoFocus
                 value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <div className="error">{error}</div>}
          <button className="btn" style={{ width: '100%', justifyContent: 'center' }} disabled={busy}>
            {busy ? '…' : 'enter'}
          </button>
          <button type="button" className="btn ghost" style={{ width: '100%', justifyContent: 'center' }}
                  onClick={() => { setSel(null); setPassword(''); setError('') }}>← back</button>
        </form>
      )}
    </div>
  )
}
