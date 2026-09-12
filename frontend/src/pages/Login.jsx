import { useState } from 'react'
import { api } from '../api'

export default function Login({ onDone }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await api.login(password)
      onDone()
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="app center" style={{ paddingTop: 100, maxWidth: 360 }}>
      <h1 style={{ marginBottom: 8 }}>khata</h1>
      <p className="muted" style={{ marginTop: 0 }}>a cozy place for your money</p>
      <form onSubmit={submit} className="card stack">
        <input type="password" placeholder="password" autoFocus
               value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <div className="error">{error}</div>}
        <button className="btn" style={{ width: '100%', justifyContent: 'center' }} disabled={busy}>
          {busy ? '…' : 'enter'}
        </button>
      </form>
    </div>
  )
}
