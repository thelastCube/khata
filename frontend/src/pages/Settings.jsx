import { useEffect, useState } from 'react'
import { api } from '../api'
import { money, useMonth } from '../components.jsx'

export default function Settings() {
  const { month, fonts, setFont, FONTS } = useMonth()
  const [funds, setFunds] = useState([])
  const [labels, setLabels] = useState([])
  const [groups, setGroups] = useState([])
  const [error, setError] = useState('')

  function reload() {
    api.funds(true).then(setFunds).catch((e) => setError(e.message))
    api.labels().then(setLabels).catch(() => {})
    api.groups().then(setGroups).catch(() => {})
  }
  useEffect(reload, [])

  const fontKinds = [['display', 'headings'], ['body', 'body text'], ['mono', 'amounts']]

  return (
    <>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h2>appearance</h2>
        {fontKinds.map(([kind, label]) => (
          <label className="field" key={kind}><span>{label} font</span>
            <select value={fonts[kind]} onChange={(e) => setFont(kind, e.target.value)}>
              {Object.keys(FONTS).map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </label>
        ))}
      </div>

      <FundsSection funds={funds} month={month} reload={reload} setError={setError} />
      <LabelsSection labels={labels} reload={reload} setError={setError} />
      <GroupsSection groups={groups} labels={labels} reload={reload} setError={setError} />

      <div className="card">
        <h2>backup</h2>
        <p className="muted small">Export every table to CSV under the server's data/exports folder.</p>
        <button className="btn ghost" onClick={async () => {
          try { const r = await api.backup(); alert(`Exported to ${r.dir}`) } catch (e) { setError(e.message) }
        }}>export CSV</button>
      </div>
    </>
  )
}

function FundsSection({ funds, month, reload, setError }) {
  const blank = { name: '', default_amount: '', default_carry_underspend: false, default_carry_overspend: false, default_emi_months: 1 }
  const [nf, setNf] = useState(blank)

  async function add() {
    if (!nf.name.trim()) return
    try {
      await api.post('/funds', {
        name: nf.name.trim(), default_amount: Number(nf.default_amount) || 0,
        default_carry_underspend: nf.default_carry_underspend, default_carry_overspend: nf.default_carry_overspend,
        default_emi_months: Number(nf.default_emi_months) || 1,
      })
      setNf(blank); reload()
    } catch (e) { setError(e.message) }
  }

  return (
    <div className="card">
      <h2>funds & budgets</h2>
      <p className="muted small" style={{ marginTop: 0 }}>Each fund has a default monthly budget. Override it for a specific month when you need to.</p>
      {funds.map((f) => <FundRow key={f.id} f={f} month={month} reload={reload} setError={setError} />)}

      <div className="stack" style={{ marginTop: 14, borderTop: '1px solid var(--line)', paddingTop: 14 }}>
        <div className="row" style={{ gap: 8 }}>
          <input type="text" placeholder="new fund name" value={nf.name} onChange={(e) => setNf({ ...nf, name: e.target.value })} />
          <input type="number" placeholder="₹ / month" style={{ maxWidth: 130 }} value={nf.default_amount}
                 onChange={(e) => setNf({ ...nf, default_amount: e.target.value })} />
        </div>
        <label className="toggle small"><input type="checkbox" checked={nf.default_carry_underspend}
          onChange={(e) => setNf({ ...nf, default_carry_underspend: e.target.checked })} /><span>roll leftover forward by default</span></label>
        <label className="toggle small"><input type="checkbox" checked={nf.default_carry_overspend}
          onChange={(e) => setNf({ ...nf, default_carry_overspend: e.target.checked })} /><span>shrink next month by overspend by default</span></label>
        <button className="btn" onClick={add} disabled={!nf.name.trim()}>add fund</button>
      </div>
    </div>
  )
}

function FundRow({ f, month, reload, setError }) {
  const [tab, setTab] = useState(null)
  async function remove() {
    if (!confirm(`Delete ${f.name}? (kept & deactivated if it has expenses)`)) return
    try { await api.del(`/funds/${f.id}`); reload() } catch (e) { setError(e.message) }
  }
  return (
    <div className="list-item">
      <div className="row between">
        <span style={{ opacity: f.active ? 1 : 0.5 }}>
          {f.name}{!f.active && ' (inactive)'} <span className="muted small">· default {money(f.default_amount)}</span>
        </span>
        <span className="row" style={{ gap: 8 }}>
          <button className="btn ghost small" onClick={() => setTab(tab === 'edit' ? null : 'edit')}>edit</button>
          <button className="btn ghost small" onClick={() => setTab(tab === 'override' ? null : 'override')}>override</button>
          <button className="btn danger small" onClick={remove}>×</button>
        </span>
      </div>
      {tab === 'edit' && <FundEditor f={f} reload={reload} setError={setError} done={() => setTab(null)} />}
      {tab === 'override' && <OverrideEditor fundId={f.id} month={month} setError={setError} />}
    </div>
  )
}

function FundEditor({ f, reload, setError, done }) {
  const [d, setD] = useState({ ...f, default_amount: f.default_amount })
  async function save() {
    try {
      await api.put(`/funds/${f.id}`, {
        name: d.name.trim(), color: f.color, sort: f.sort, active: d.active,
        default_amount: Number(d.default_amount) || 0,
        default_carry_underspend: d.default_carry_underspend, default_carry_overspend: d.default_carry_overspend,
        default_emi_months: Number(d.default_emi_months) || 1,
      })
      reload(); done()
    } catch (e) { setError(e.message) }
  }
  return (
    <div className="stack sub">
      <div className="muted small">default budget (case of the name is kept; rename anytime)</div>
      <div className="row" style={{ gap: 8 }}>
        <input type="text" value={d.name} onChange={(e) => setD({ ...d, name: e.target.value })} />
        <input type="number" style={{ maxWidth: 130 }} value={d.default_amount} onChange={(e) => setD({ ...d, default_amount: e.target.value })} />
      </div>
      <label className="toggle small"><input type="checkbox" checked={d.default_carry_underspend}
        onChange={(e) => setD({ ...d, default_carry_underspend: e.target.checked })} /><span>roll leftover forward</span></label>
      <label className="toggle small"><input type="checkbox" checked={d.default_carry_overspend}
        onChange={(e) => setD({ ...d, default_carry_overspend: e.target.checked })} /><span>shrink next month by overspend</span></label>
      {d.default_carry_overspend && (
        <label className="field" style={{ marginBottom: 4 }}><span>spread repayment over N months</span>
          <input type="number" min="1" value={d.default_emi_months} onChange={(e) => setD({ ...d, default_emi_months: e.target.value })} /></label>
      )}
      <label className="toggle small"><input type="checkbox" checked={d.active}
        onChange={(e) => setD({ ...d, active: e.target.checked })} /><span>active</span></label>
      <button className="btn small" onClick={save}>save fund</button>
    </div>
  )
}

function OverrideEditor({ fundId, month, setError }) {
  const [b, setB] = useState(null)
  const [ok, setOk] = useState('')
  function load() { api.budget(fundId, month).then(setB).catch((e) => setError(e.message)) }
  useEffect(load, [fundId, month])
  if (!b) return <div className="muted small sub">…</div>

  async function save() {
    try {
      await api.setBudget(fundId, month, {
        amount: Number(b.amount), carry_underspend: b.carry_underspend,
        carry_overspend: b.carry_overspend, emi_months: Number(b.emi_months) || 1,
      })
      setOk('override saved'); setTimeout(() => setOk(''), 1500); load()
    } catch (e) { setError(e.message) }
  }
  async function revert() {
    try { await api.del(`/budgets/${fundId}?month=${month}`); setOk('reverted to default'); setTimeout(() => setOk(''), 1500); load() }
    catch (e) { setError(e.message) }
  }

  return (
    <div className="stack sub">
      <div className="muted small">
        {b.is_override ? `overriding ${month}` : `using the fund default for ${month}`}
      </div>
      <label className="field" style={{ marginBottom: 4 }}><span>budget for {month}</span>
        <input type="number" value={b.amount} onChange={(e) => setB({ ...b, amount: e.target.value })} /></label>
      <label className="toggle small"><input type="checkbox" checked={b.carry_underspend}
        onChange={(e) => setB({ ...b, carry_underspend: e.target.checked })} /><span>roll leftover forward</span></label>
      <label className="toggle small"><input type="checkbox" checked={b.carry_overspend}
        onChange={(e) => setB({ ...b, carry_overspend: e.target.checked })} /><span>shrink next month by overspend</span></label>
      {b.carry_overspend && (
        <label className="field" style={{ marginBottom: 4 }}><span>spread repayment over N months</span>
          <input type="number" min="1" value={b.emi_months} onChange={(e) => setB({ ...b, emi_months: e.target.value })} /></label>
      )}
      <div className="row" style={{ gap: 8 }}>
        <button className="btn small" onClick={save}>save override</button>
        {b.is_override && <button className="btn ghost small" onClick={revert}>revert to default</button>}
        {ok && <span className="ok">{ok}</span>}
      </div>
    </div>
  )
}

function LabelsSection({ labels, reload, setError }) {
  const [name, setName] = useState('')
  async function add() {
    if (!name.trim()) return
    try { await api.post('/labels', { name: name.trim() }); setName(''); reload() } catch (e) { setError(e.message) }
  }
  return (
    <div className="card">
      <h2>labels</h2>
      <div className="tags">
        {labels.map((l) => (
          <span key={l.id} className="tag">{l.name}
            <button onClick={async () => { if (confirm(`Delete label ${l.name}?`)) { await api.del(`/labels/${l.id}`); reload() } }}>×</button>
          </span>
        ))}
        {labels.length === 0 && <span className="muted">none yet — they're also created on the fly when you add expenses</span>}
      </div>
      <div className="row" style={{ gap: 8, marginTop: 12 }}>
        <input type="text" placeholder="new label" value={name}
               onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && add()} />
        <button className="btn" onClick={add}>add</button>
      </div>
    </div>
  )
}

function GroupsSection({ groups, labels, reload, setError }) {
  const [name, setName] = useState('')
  const [picked, setPicked] = useState([])
  const labelName = Object.fromEntries(labels.map((l) => [l.id, l.name]))
  async function add() {
    if (!name.trim()) return
    try { await api.post('/groups', { name: name.trim(), label_ids: picked }); setName(''); setPicked([]); reload() }
    catch (e) { setError(e.message) }
  }
  return (
    <div className="card">
      <h2>groups <span className="muted small">(saved sets of labels)</span></h2>
      {groups.map((g) => (
        <div key={g.id} className="list-item row between">
          <span>{g.name} <span className="muted small">— {g.label_ids.map((id) => labelName[id]).filter(Boolean).join(', ') || 'empty'}</span></span>
          <button className="btn danger small" onClick={async () => { if (confirm(`Delete group ${g.name}?`)) { await api.del(`/groups/${g.id}`); reload() } }}>×</button>
        </div>
      ))}
      <div className="stack" style={{ marginTop: 12 }}>
        <input type="text" placeholder="new group name" value={name} onChange={(e) => setName(e.target.value)} />
        <div className="tags">
          {labels.map((l) => {
            const on = picked.includes(l.id)
            return <button key={l.id} type="button" className="tag" style={{ opacity: on ? 1 : 0.45 }}
              onClick={() => setPicked(on ? picked.filter((x) => x !== l.id) : [...picked, l.id])}>{l.name}</button>
          })}
        </div>
        <button className="btn" onClick={add} disabled={!name.trim()}>create group</button>
      </div>
    </div>
  )
}
