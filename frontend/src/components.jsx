import { createContext, useContext, useEffect, useRef, useState } from 'react'

export const MonthContext = createContext(null)
export const useMonth = () => useContext(MonthContext)

export function thisMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const inr = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })
export function money(n) {
  const v = Math.round(Number(n) || 0)
  return (v < 0 ? '−₹' : '₹') + inr.format(Math.abs(v))
}

export function Money({ value, className = '' }) {
  return <span className={`amount ${className}`}>{money(value)}</span>
}

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function MonthPicker() {
  const { month, setMonth } = useMonth()
  const [open, setOpen] = useState(false)
  const [year, setYear] = useState(() => parseInt(month.split('-')[0], 10))
  const ref = useRef(null)

  useEffect(() => {
    function onDoc(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const [y, m] = month.split('-')
  const label = `${MON[parseInt(m, 10) - 1]} ${y}`
  function pick(i) { setMonth(`${year}-${String(i + 1).padStart(2, '0')}`); setOpen(false) }

  return (
    <div className="monthpicker" ref={ref}>
      <button className="btn ghost small" onClick={() => { setYear(parseInt(y, 10)); setOpen(!open) }}>
        {label} ▾
      </button>
      {open && (
        <div className="pop">
          <div className="row between yr">
            <button className="btn ghost small" onClick={() => setYear(year - 1)}>‹</button>
            <b className="num">{year}</b>
            <button className="btn ghost small" onClick={() => setYear(year + 1)}>›</button>
          </div>
          <div className="month-grid">
            {MON.map((mm, i) => {
              const active = year === parseInt(y, 10) && i === parseInt(m, 10) - 1
              return <button key={mm} className={`mbtn ${active ? 'active' : ''}`} onClick={() => pick(i)}>{mm}</button>
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// pills — still used on the fund-detail page
export function Pills({ row }) {
  return (
    <div className="pills">
      <span className="pill budget">budget {money(row.base)}</span>
      {row.carry ? (
        <span className="pill carry">carried over {money(row.carry)}</span>
      ) : null}
      {row.transfers_in ? <span className="pill blue">siphoned in {money(row.transfers_in)}</span> : null}
      {row.transfers_out ? <span className="pill blue">moved out {money(row.transfers_out)}</span> : null}
      {row.overage > 0 ? (
        <span className="pill over">exceeded {money(row.overage)}</span>
      ) : (
        <span className="pill good">left {money(row.remaining)}</span>
      )}
    </div>
  )
}
