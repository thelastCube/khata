import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Money, money, useMonth } from '../components.jsx'
import { FundMonthGrid, HeatLegend, HistoryGrid, MonthSquares } from '../heatmap.jsx'

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export default function Analysis() {
  const { month } = useMonth()
  const [labels, setLabels] = useState([])
  const [groups, setGroups] = useState([])
  const [funds, setFunds] = useState([])

  const [year, setYear] = useState(() => parseInt(month.split('-')[0], 10))
  const [selected, setSelected] = useState(() => [month]) // ['YYYY-MM', ...]
  const [picked, setPicked] = useState([])
  const [groupId, setGroupId] = useState('')
  const [fundId, setFundId] = useState('')

  const [res, setRes] = useState(null)
  const [heat, setHeat] = useState(null)
  const [history, setHistory] = useState(null)
  const [increment, setIncrement] = useState(() => Number(localStorage.getItem('hm_increment')) || 2000)
  const [heatMode, setHeatMode] = useState('month') // when >2 months
  const [error, setError] = useState('')

  const months = useMemo(() => [...selected].sort(), [selected])

  useEffect(() => {
    api.labels().then(setLabels).catch(() => {})
    api.groups().then(setGroups).catch(() => {})
    api.funds(true).then(setFunds).catch(() => {})
    api.history().then(setHistory).catch(() => {})
  }, [])
  useEffect(() => { localStorage.setItem('hm_increment', String(increment)) }, [increment])

  useEffect(() => {
    setError('')
    if (months.length === 0) { setRes(null); setHeat(null); return }
    const p = new URLSearchParams()
    months.forEach((m) => p.append('months', m))
    if (fundId) p.set('fund_id', fundId)
    if (groupId) p.set('group_id', groupId)
    picked.forEach((id) => p.append('label_ids', id))
    api.analysis(p.toString()).then(setRes).catch((e) => setError(e.message))
    api.heatmap(months).then(setHeat).catch(() => setHeat(null))
  }, [months, picked, groupId, fundId])

  function toggleMonth(i) {
    const m = `${year}-${String(i + 1).padStart(2, '0')}`
    setSelected((s) => s.includes(m) ? s.filter((x) => x !== m) : [...s, m])
  }
  const wholeYear = () => setSelected(MON.map((_, i) => `${year}-${String(i + 1).padStart(2, '0')}`))
  const thisMonthOnly = () => { const y = parseInt(month.split('-')[0], 10); setYear(y); setSelected([month]) }

  const fundName = Object.fromEntries(funds.map((f) => [f.id, f.name]))
  // per-fund budget context aggregated over the selected months (from heatmap cells)
  const fundBudget = useMemo(() => {
    const agg = {}
    heat?.cells.forEach((c) => {
      const a = agg[c.fund_id] || (agg[c.fund_id] = { base: 0, spent: 0 })
      a.base += c.base; a.spent += c.spent
    })
    return agg
  }, [heat])

  return (
    <>
      <div className="card">
        <h2>analyse</h2>

        <div className="row between" style={{ marginBottom: 10 }}>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn ghost small" onClick={() => setYear(year - 1)}>‹</button>
            <b className="num">{year}</b>
            <button className="btn ghost small" onClick={() => setYear(year + 1)}>›</button>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn ghost small" onClick={thisMonthOnly}>this month</button>
            <button className="btn ghost small" onClick={wholeYear}>whole year</button>
            <button className="btn ghost small" onClick={() => setSelected([])}>clear</button>
          </div>
        </div>

        <div className="month-chips">
          {MON.map((mm, i) => {
            const on = selected.includes(`${year}-${String(i + 1).padStart(2, '0')}`)
            return <button key={mm} type="button" className={`chip ${on ? 'on' : ''}`} onClick={() => toggleMonth(i)}>{mm}</button>
          })}
        </div>
        <div className="small muted" style={{ marginTop: 8 }}>
          {months.length === 0 ? 'pick one or more months' : months.map((m) => `${MON[parseInt(m.split('-')[1], 10) - 1]} ${m.split('-')[0]}`).join(', ')}
        </div>

        <div className="muted small" style={{ margin: '14px 0 6px' }}>labels (an expense must have all selected)</div>
        <div className="tags" style={{ marginBottom: 14 }}>
          {labels.map((l) => {
            const on = picked.includes(l.id)
            return <button key={l.id} type="button" className="tag" style={{ opacity: on ? 1 : 0.45 }}
              onClick={() => setPicked(on ? picked.filter((x) => x !== l.id) : [...picked, l.id])}>{l.name}</button>
          })}
          {labels.length === 0 && <span className="muted">no labels yet</span>}
        </div>
        <div className="grid2">
          <label className="field"><span>group</span>
            <select value={groupId} onChange={(e) => setGroupId(e.target.value)}>
              <option value="">— any —</option>
              {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select></label>
          <label className="field"><span>fund</span>
            <select value={fundId} onChange={(e) => setFundId(e.target.value)}>
              <option value="">— any —</option>
              {funds.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
            </select></label>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* heatmap — final state (budget vs spent), green under / red over */}
      {heat && months.length > 0 && (
        <div className="card">
          <div className="row between" style={{ marginBottom: 4 }}>
            <h2>heatmap</h2>
            <label className="row small" style={{ gap: 6 }}>
              <span className="muted">shade step ₹</span>
              <input type="number" min="1" style={{ width: 90, padding: '6px 8px' }}
                     value={increment} onChange={(e) => setIncrement(Number(e.target.value) || 1)} />
            </label>
          </div>
          <p className="muted small" style={{ marginTop: 0 }}>Final state only — budget vs spent. Green = under, red = over.</p>
          {months.length > 2 && (
            <div className="row" style={{ gap: 8, marginBottom: 10 }}>
              <button className={`btn ghost small ${heatMode === 'fund' ? 'sel' : ''}`} onClick={() => setHeatMode('fund')}>by fund</button>
              <button className={`btn ghost small ${heatMode === 'month' ? 'sel' : ''}`} onClick={() => setHeatMode('month')}>one square per month</button>
            </div>
          )}
          {months.length <= 2 || heatMode === 'fund'
            ? <FundMonthGrid data={heat} increment={increment} />
            : <MonthSquares monthTotals={heat.month_totals} increment={increment} />}
          <div style={{ marginTop: 10 }}><HeatLegend increment={increment} /></div>
        </div>
      )}

      {res && (
        <>
          <div className="card center">
            <div className="muted small">{res.count} expense(s) across {months.length} month(s)</div>
            <Money value={res.total} className="big" />
          </div>

          {res.by_fund.length > 0 && (
            <div className="card">
              <h2>by fund</h2>
              {res.by_fund.map((r) => {
                const b = fundBudget[r.fund_id]
                const net = b ? b.base - b.spent : null
                return (
                  <div key={r.fund_id} className="list-item row between">
                    <div>
                      <div>{r.name}</div>
                      {b && (
                        <div className="small muted">
                          budget {money(b.base)}
                          {net >= 0 ? <span className="c-good"> · {money(net)} under</span> : <span className="c-over"> · {money(-net)} over</span>}
                        </div>
                      )}
                    </div>
                    <Money value={r.total} />
                  </div>
                )
              })}
            </div>
          )}

          {res.by_label.length > 0 && (
            <div className="card">
              <h2>by label</h2>
              {res.by_label.map((r) => (
                <div key={r.label_id} className="list-item row between"><span>{r.name}</span><Money value={r.total} /></div>
              ))}
            </div>
          )}

          <div className="card">
            <h2>matching expenses</h2>
            {res.expenses.length === 0 && <div className="muted">none</div>}
            {res.expenses.map((e) => (
              <div key={e.id} className="list-item row between">
                <span><span className="mono small muted">{e.ts.slice(0, 10)}</span> · {fundName[e.fund_id]} {e.note ? `· ${e.note}` : ''}</span>
                <Money value={e.amount} />
              </div>
            ))}
          </div>
        </>
      )}

      {history && history.months.length > 0 && (
        <div className="card">
          <h2>all history</h2>
          <p className="muted small" style={{ marginTop: 0 }}>Every month as a square — green months you stayed under budget, red you went over.</p>
          <HistoryGrid history={history} increment={increment} />
          <div style={{ marginTop: 10 }}><HeatLegend increment={increment} /></div>
        </div>
      )}
    </>
  )
}
