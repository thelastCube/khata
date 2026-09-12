import { useEffect, useState } from 'react'
import { api } from '../api'
import { useMonth } from '../components.jsx'

export default function Audit() {
  const { month } = useMonth()
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { api.audit(month).then(setRows).catch((e) => setError(e.message)) }, [month])

  if (error) return <div className="error">{error}</div>
  if (!rows) return <div className="muted">…</div>

  return (
    <div className="card">
      <h2>log — {month}</h2>
      {rows.length === 0 && <div className="muted">Nothing happened this month.</div>}
      {rows.map((r) => (
        <div key={r.id} className="list-item">
          <div className="row between">
            <b>{r.action}</b>
            <span className="mono small muted">{r.ts.replace('T', ' ').slice(0, 16)}</span>
          </div>
          {r.detail && <div className="small muted mono" style={{ wordBreak: 'break-word' }}>{JSON.stringify(r.detail)}</div>}
        </div>
      ))}
    </div>
  )
}
