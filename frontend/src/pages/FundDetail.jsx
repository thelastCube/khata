import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'
import { Money, money, Pills, useMonth } from '../components.jsx'

export default function FundDetail() {
  const { id } = useParams()
  const { month } = useMonth()
  const [d, setD] = useState(null)
  const [labels, setLabels] = useState({})
  const [error, setError] = useState('')
  const [balancing, setBalancing] = useState(false)
  const [suggestions, setSuggestions] = useState([])

  function load() {
    setError('')
    api.fundDetail(id, month).then(setD).catch((e) => setError(e.message))
  }
  useEffect(load, [id, month])
  useEffect(() => { api.labels().then((ls) => setLabels(Object.fromEntries(ls.map((l) => [l.id, l.name])))).catch(() => {}) }, [])

  async function openBalance() {
    setBalancing(true)
    setSuggestions(await api.balanceSuggestions(id, month))
  }
  async function siphon(fromId, max) {
    const raw = prompt(`Move how much from that fund to cover ${d.fund.name}? (max ${money(max)})`, String(Math.min(max, d.overage || max)))
    if (!raw) return
    try {
      await api.transfer({ month, from_fund_id: fromId, to_fund_id: Number(id), amount: Number(raw), reason: `balance ${d.fund.name}` })
      setBalancing(false); load()
    } catch (e) { setError(e.message) }
  }

  if (error) return <div className="error">{error}</div>
  if (!d) return <div className="muted">…</div>

  return (
    <>
      <div className="card">
        <div className="row between">
          <h1>{d.fund.name}</h1>
          <div className="center">
            <Money value={d.spent} className={`big ${d.overage > 0 ? 'over' : ''}`} />
            <div className="muted small">of {money(d.available)} available</div>
          </div>
        </div>
        <div style={{ marginTop: 12 }}><Pills row={d} /></div>
        <div className="row" style={{ gap: 20, marginTop: 14 }}>
          <span className="muted small">vs last month:&nbsp;
            <b className={d.delta_vs_prev > 0 ? 'amount over' : 'amount'}>
              {d.delta_vs_prev >= 0 ? '+' : ''}{money(d.delta_vs_prev)}</b></span>
        </div>
        {d.overage > 0 && (
          <button className="btn ghost" style={{ marginTop: 14 }} onClick={openBalance}>balance this overage</button>
        )}
      </div>

      {balancing && (
        <div className="card">
          <h2>pull from a fund with a surplus</h2>
          {suggestions.length === 0 && <div className="muted">No funds have spare budget this month.</div>}
          {suggestions.map((s) => (
            <div key={s.fund.id} className="list-item row between">
              <span>{s.fund.name}</span>
              <span className="row" style={{ gap: 12 }}>
                <span className="pill good">spare {money(s.surplus)}</span>
                <button className="btn small" onClick={() => siphon(s.fund.id, s.surplus)}>use</button>
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h2>expenses</h2>
        {d.expenses.length === 0 && <div className="muted">Nothing logged this month.</div>}
        {d.expenses.map((e) => (
          <div key={e.id} className="list-item row between">
            <div>
              <div className="mono small muted">{e.ts.replace('T', ' ').slice(0, 16)}</div>
              <div>{e.note || <span className="muted">—</span>}</div>
              <div className="tags" style={{ marginTop: 4 }}>
                {e.label_ids.map((lid) => <span key={lid} className="tag">{labels[lid] || lid}</span>)}
              </div>
            </div>
            <Money value={e.amount} />
          </div>
        ))}
      </div>

      {(d.transfers.length > 0 || d.carry_adjustments.length > 0) && (
        <div className="card">
          <h2>traceability</h2>
          {d.carry_adjustments.map((a, i) => (
            <div key={`c${i}`} className="list-item small">
              {a.kind === 'underspend_rollin'
                ? `carried over (leftover from ${a.source_month})`
                : `carried over (making up ${a.source_month}'s overspend)`}: <b className="amount">{money(a.amount)}</b>
              {a.emi_remaining > 0 && <span className="muted"> · {a.emi_remaining} more month(s)</span>}
            </div>
          ))}
          {d.transfers.map((t) => (
            <div key={t.id} className="list-item small">
              {t.direction === 'in'
                ? <>siphoned in from <b>{t.from_name}</b></>
                : <>moved out to <b>{t.to_name}</b></>} <b className="amount">{money(t.amount)}</b>
              {t.reason && <span className="muted"> — {t.reason}</span>}
              <span className="muted"> · {t.ts.replace('T', ' ').slice(0, 16)}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
