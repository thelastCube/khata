import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Money, money, useMonth } from '../components.jsx'

export default function Overview() {
  const { month } = useMonth()
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  function load() {
    setError('')
    api.overview(month).then(setRows).catch((e) => setError(e.message))
  }
  useEffect(load, [month])

  async function close() {
    if (!confirm(`Close ${month}? Rolls leftovers forward and schedules overspend repayments, per each fund's carry settings.`)) return
    try { const r = await api.closeMonth(month); setMsg(`closed — ${r.applied.length} adjustment(s) applied`); load() }
    catch (e) { setError(e.message) }
  }

  if (error) return <div className="error">{error}</div>
  if (!rows) return <div className="muted">…</div>

  const totalSpent = rows.reduce((a, r) => a + r.spent, 0)
  const totalAvail = rows.reduce((a, r) => a + r.available, 0)

  return (
    <>
      <div className="card">
        <div className="row between">
          <div>
            <div className="muted small">spent this month</div>
            <Money value={totalSpent} className="big" />
          </div>
          <div className="right">
            <div className="muted small">of {money(totalAvail)} available</div>
          </div>
        </div>
      </div>

      {msg && <div className="ok">{msg}</div>}
      {rows.length === 0 && <div className="card muted center">No funds yet — add some in settings.</div>}

      {rows.map((r) => {
        const over = r.overage > 0
        const pct = r.available > 0 ? Math.min(100, (r.spent / r.available) * 100) : (r.spent > 0 ? 100 : 0)
        return (
          <Link key={r.fund_id} to={`/funds/${r.fund_id}`} className="card fund-row">
            <div className="row between" style={{ alignItems: 'baseline' }}>
              <span className="name">{r.fund.name}</span>
              <Money value={r.spent} className={`big ${over ? 'over' : 'good'}`} />
            </div>

            <div className="bar"><span className={over ? 'over' : 'good'} style={{ width: `${pct}%` }} /></div>

            <Stats row={r} over={over} />
          </Link>
        )
      })}

      <button className="btn ghost" style={{ marginTop: 8 }} onClick={close}>close {month}</button>
    </>
  )
}

// Always four cells in fixed positions: budget · left/exceeded · carried over · siphoned.
// Missing ones render as empty cells so every card lines up.
function Stats({ row, over }) {
  const slots = [
    { value: money(row.base), label: 'budget', tone: 'muted' },
    over
      ? { value: money(row.overage), label: 'exceeded', tone: 'over' }
      : { value: money(row.remaining), label: 'left', tone: 'good' },
    row.carry ? { value: money(row.carry), label: row.carry > 0 ? 'carried over' : 'repaying', tone: 'carry' } : null,
    row.transfers_in
      ? { value: money(row.transfers_in), label: 'siphoned in', tone: 'blue' }
      : (row.transfers_out ? { value: money(-row.transfers_out), label: 'moved out', tone: 'blue' } : null),
  ]
  return (
    <div className="stats">
      {slots.map((s, i) => s
        ? <span key={i} className={`stat ${s.tone}`}><b className="num">{s.value}</b><span className="k">{s.label}</span></span>
        : <span key={i} className="stat empty" />)}
    </div>
  )
}
