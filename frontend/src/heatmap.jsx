import { money } from './components.jsx'

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const ALPHA = [0.16, 0.34, 0.52, 0.72, 0.92]

// Final-state colour: green when under budget (net >= 0), red when over.
// Darker with each `increment` rupees of over/under. Empty = no budget, no spend.
export function shade(net, increment, empty) {
  if (empty) return 'transparent'
  const inc = Math.max(1, increment)
  const level = Math.min(4, Math.floor(Math.abs(net) / inc))
  const rgb = net >= 0 ? '79, 122, 91' : '192, 73, 47'
  return `rgba(${rgb}, ${ALPHA[level]})`
}

function label(m) {
  const [y, mm] = m.split('-')
  return `${MON[parseInt(mm, 10) - 1]} ${y}`
}

// rows = funds, columns = months
export function FundMonthGrid({ data, increment }) {
  const byKey = {}
  data.cells.forEach((c) => { byKey[`${c.fund_id}:${c.month}`] = c })
  return (
    <div className="hm-scroll">
      <table className="hm">
        <thead>
          <tr>
            <th />
            {data.months.map((m) => <th key={m} className="hm-col">{label(m)}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.funds.map((f) => (
            <tr key={f.id}>
              <th className="hm-row">{f.name}</th>
              {data.months.map((m) => {
                const c = byKey[`${f.id}:${m}`] || { net: 0, base: 0, spent: 0 }
                const empty = c.base === 0 && c.spent === 0
                return (
                  <td key={m}>
                    <span className="cell" style={{ background: shade(c.net, increment, empty) }}
                          title={`${f.name} · ${label(m)}\nbudget ${money(c.base)} · spent ${money(c.spent)}\n${c.net >= 0 ? money(c.net) + ' under' : money(-c.net) + ' over'}`} />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// one square per month (collapsed view for many months)
export function MonthSquares({ monthTotals, increment }) {
  return (
    <div className="hm-months">
      {monthTotals.map((t) => {
        const empty = t.base === 0 && t.spent === 0
        return (
          <div key={t.month} className="hm-month">
            <span className="cell big" style={{ background: shade(t.net, increment, empty) }}
                  title={`${label(t.month)}\nbudget ${money(t.base)} · spent ${money(t.spent)}\n${t.net >= 0 ? money(t.net) + ' under' : money(-t.net) + ' over'}`} />
            <span className="hm-mlabel">{label(t.month).split(' ')[0]}</span>
          </div>
        )
      })}
    </div>
  )
}

// GitHub-style: each row a year, 12 columns Jan–Dec
export function HistoryGrid({ history, increment }) {
  const byMonth = {}
  history.month_totals.forEach((t) => { byMonth[t.month] = t })
  const years = [...new Set(history.months.map((m) => m.split('-')[0]))]
  return (
    <div className="hm-scroll">
      <table className="hm history">
        <thead>
          <tr><th />{MON.map((m) => <th key={m} className="hm-col">{m}</th>)}</tr>
        </thead>
        <tbody>
          {years.map((y) => (
            <tr key={y}>
              <th className="hm-row">{y}</th>
              {MON.map((_, i) => {
                const key = `${y}-${String(i + 1).padStart(2, '0')}`
                const t = byMonth[key]
                if (!t) return <td key={i}><span className="cell" /></td>
                const empty = t.base === 0 && t.spent === 0
                return (
                  <td key={i}>
                    <span className="cell" style={{ background: shade(t.net, increment, empty) }}
                          title={`${label(key)}\nbudget ${money(t.base)} · spent ${money(t.spent)}\n${t.net >= 0 ? money(t.net) + ' under' : money(-t.net) + ' over'}`} />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function HeatLegend({ increment }) {
  return (
    <div className="hm-legend small muted">
      <span>over</span>
      {[4, 3, 2, 1].map((l) => <span key={`r${l}`} className="cell sm" style={{ background: `rgba(192,73,47,${ALPHA[l]})` }} />)}
      <span className="cell sm" style={{ background: 'transparent', border: '1px solid var(--line)' }} />
      {[1, 2, 3, 4].map((l) => <span key={`g${l}`} className="cell sm" style={{ background: `rgba(79,122,91,${ALPHA[l]})` }} />)}
      <span>under · each step ≈ {money(increment)}</span>
    </div>
  )
}
