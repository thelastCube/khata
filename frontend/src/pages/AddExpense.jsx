import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

export default function AddExpense() {
  const [funds, setFunds] = useState([])
  const [labels, setLabels] = useState([])
  const [amount, setAmount] = useState('')
  const [fundId, setFundId] = useState('')
  const [tags, setTags] = useState([])
  const [note, setNote] = useState('')
  const [when, setWhen] = useState(() => new Date().toISOString().slice(0, 10))
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  useEffect(() => {
    api.funds().then((f) => { setFunds(f); if (f[0]) setFundId(String(f[0].id)) }).catch((e) => setError(e.message))
    api.labels().then(setLabels).catch(() => {})
  }, [])

  async function submit(e) {
    e.preventDefault()
    setError(''); setOk('')
    try {
      await api.post('/expenses', {
        amount: Number(amount), fund_id: Number(fundId), labels: tags,
        ts: `${when}T12:00:00`, note: note || null,
      })
      setOk(`added ₹${amount}`)
      setAmount(''); setTags([]); setNote('')
      api.labels().then(setLabels).catch(() => {})
    } catch (err) { setError(err.message) }
  }

  return (
    <form onSubmit={submit} className="card stack">
      <h2>add an expense</h2>
      <input className="amount-input" type="number" inputMode="decimal" placeholder="0"
             value={amount} onChange={(e) => setAmount(e.target.value)} autoFocus />

      <label className="field">
        <span>fund</span>
        <select value={fundId} onChange={(e) => setFundId(e.target.value)}>
          {funds.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>
      </label>

      <label className="field">
        <span>labels</span>
        <LabelInput labels={labels} tags={tags} setTags={setTags} />
      </label>

      <div className="grid2">
        <label className="field"><span>date</span>
          <input type="date" value={when} onChange={(e) => setWhen(e.target.value)} /></label>
        <label className="field"><span>note</span>
          <input type="text" value={note} onChange={(e) => setNote(e.target.value)} placeholder="optional" /></label>
      </div>

      {error && <div className="error">{error}</div>}
      {ok && <div className="ok">{ok}</div>}
      <button className="btn" disabled={!amount || !fundId}>save</button>
    </form>
  )
}

function LabelInput({ labels, tags, setTags }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)

  // canonical-name match, case-insensitive
  const pickedLower = tags.map((t) => t.toLowerCase())
  const suggestions = useMemo(() => {
    const s = q.trim().toLowerCase()
    return labels
      .filter((l) => !pickedLower.includes(l.name.toLowerCase()))
      .filter((l) => (s ? l.name.toLowerCase().includes(s) : true))
      .slice(0, 6)
  }, [q, labels, tags])

  function add(name) {
    const v = name.trim()
    if (!v) return
    // reuse an existing label's canonical name if it matches case-insensitively
    const existing = labels.find((l) => l.name.toLowerCase() === v.toLowerCase())
    const finalName = existing ? existing.name : v
    if (!tags.some((t) => t.toLowerCase() === finalName.toLowerCase())) setTags([...tags, finalName])
    setQ(''); setOpen(false)
  }

  return (
    <>
      <div className="tags" style={{ marginBottom: 8 }}>
        {tags.map((t) => (
          <span key={t} className="tag">{t}
            <button type="button" onClick={() => setTags(tags.filter((x) => x !== t))}>×</button>
          </span>
        ))}
      </div>
      <div className="autocomplete">
        <input type="text" placeholder="type a label — pick one or press Enter to create"
               value={q}
               onChange={(e) => { setQ(e.target.value); setOpen(true) }}
               onFocus={() => setOpen(true)}
               onBlur={() => setTimeout(() => setOpen(false), 120)}
               onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add(q) } }} />
        {open && (suggestions.length > 0 || q.trim()) && (
          <div className="suggestions">
            {suggestions.map((l) => (
              <button type="button" key={l.id} className="sugg" onMouseDown={() => add(l.name)}>{l.name}</button>
            ))}
            {q.trim() && !labels.some((l) => l.name.toLowerCase() === q.trim().toLowerCase()) && (
              <button type="button" className="sugg create" onMouseDown={() => add(q)}>+ create “{q.trim()}”</button>
            )}
          </div>
        )}
      </div>
    </>
  )
}
