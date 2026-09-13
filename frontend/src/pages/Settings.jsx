import { useEffect, useState } from 'react'
import { api } from '../api'
import { Avatar, AvatarCropper, money, useMonth } from '../components.jsx'

const SWATCH = { bee: '#c1902f', ladybug: '#c04a3d', shark: '#3f6f9f', caterpillar: '#4f8a5b' }

export default function Settings() {
  const { month, fonts, setFont, FONTS, profile, refreshProfile, accent, setAccent, ACCENTS } = useMonth()
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
        <div className="field">
          <span className="muted small" style={{ display: 'block', marginBottom: 8 }}>theme</span>
          <div className="swatches">
            {ACCENTS.map((a) => (
              <button key={a} type="button" className={`swatch ${accent === a ? 'on' : ''}`} onClick={() => setAccent(a)}>
                <span className="dot" data-accent={a} style={{ background: SWATCH[a] }} />
                {a}
              </button>
            ))}
          </div>
        </div>
        {fontKinds.map(([kind, label]) => (
          <label className="field" key={kind}><span>{label} font</span>
            <select value={fonts[kind]} onChange={(e) => setFont(kind, e.target.value)}>
              {Object.keys(FONTS).map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </label>
        ))}
      </div>

      <AccountSection profile={profile} refreshProfile={refreshProfile} setError={setError} />
      {profile?.is_admin && <ProfilesSection profile={profile} setError={setError} />}

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

      <div className="card">
        <button className="btn ghost" style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => api.logout().then(() => location.reload())}>log out</button>
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

function AccountSection({ profile, refreshProfile, setError }) {
  const [cur, setCur] = useState('')
  const [nw, setNw] = useState('')
  const [confirm, setConfirm] = useState('')
  const [ok, setOk] = useState('')
  const [cropFile, setCropFile] = useState(null)

  async function changePw() {
    if (nw !== confirm) { setError('new passwords do not match'); return }
    try {
      await api.changePassword(cur, nw)
      setOk('password changed'); setTimeout(() => setOk(''), 2000)
      setCur(''); setNw(''); setConfirm('')
      refreshProfile()
    } catch (e) { setError(e.message) }
  }
  async function setEmoji() {
    const v = prompt('Enter an emoji for your avatar')
    if (v) { try { await api.setAvatar(v.trim()); refreshProfile() } catch (e) { setError(e.message) } }
  }
  function uploadPhoto(e) {
    const f = e.target.files?.[0]
    if (f) setCropFile(f)
    e.target.value = ''
  }

  return (
    <div className="card">
      {cropFile && (
        <AvatarCropper file={cropFile} onCancel={() => setCropFile(null)}
          onDone={async (url) => {
            try { await api.setAvatar(url); refreshProfile() } catch (err) { setError(err.message) }
            setCropFile(null)
          }} />
      )}
      <h2>account</h2>
      {profile?.must_change_password && (
        <div className="banner">You're on a starter password — set your own below.</div>
      )}
      <div className="row" style={{ gap: 14, marginBottom: 14 }}>
        <Avatar value={profile?.avatar} size={56} />
        <div>
          <div><b>{profile?.name}</b>{profile?.is_admin && <span className="muted small"> · admin</span>}</div>
          <div className="row" style={{ gap: 8, marginTop: 8 }}>
            <button className="btn ghost small" onClick={setEmoji}>set emoji</button>
            <label className="btn ghost small">upload photo
              <input type="file" accept="image/*" hidden onChange={uploadPhoto} /></label>
          </div>
        </div>
      </div>
      <div className="stack">
        <div className="muted small">change password</div>
        <input type="password" placeholder="current password" value={cur} onChange={(e) => setCur(e.target.value)} />
        <input type="password" placeholder="new password" value={nw} onChange={(e) => setNw(e.target.value)} />
        <input type="password" placeholder="confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        <div className="row" style={{ gap: 8 }}>
          <button className="btn small" onClick={changePw} disabled={!cur || !nw}>update password</button>
          {ok && <span className="ok">{ok}</span>}
        </div>
      </div>
    </div>
  )
}

function ProfilesSection({ profile, setError }) {
  const blank = { name: '', password: '', avatar: '', is_admin: false }
  const [users, setUsers] = useState([])
  const [nf, setNf] = useState(blank)
  const [cropFile, setCropFile] = useState(null)

  function reload() { api.listUsers().then(setUsers).catch((e) => setError(e.message)) }
  useEffect(reload, [])

  async function add() {
    if (!nf.name.trim() || !nf.password) return
    try {
      await api.createUser({ name: nf.name.trim(), password: nf.password, avatar: nf.avatar || null, is_admin: nf.is_admin })
      setNf(blank); reload()
    } catch (e) { setError(e.message) }
  }
  async function reset(u) {
    const p = prompt(`New password for ${u.name}`)
    if (p) { try { await api.resetPassword(u.id, p); alert(`Password reset for ${u.name}`) } catch (e) { setError(e.message) } }
  }
  async function del(u) {
    if (confirm(`Delete profile ${u.name} and ALL their data? This can't be undone.`)) {
      try { await api.deleteUser(u.id); reload() } catch (e) { setError(e.message) }
    }
  }
  function uploadPhoto(e) {
    const f = e.target.files?.[0]
    if (f) setCropFile(f)
    e.target.value = ''
  }

  return (
    <div className="card">
      {cropFile && (
        <AvatarCropper file={cropFile} onCancel={() => setCropFile(null)}
          onDone={(url) => { setNf((prev) => ({ ...prev, avatar: url })); setCropFile(null) }} />
      )}
      <h2>profiles <span className="muted small">(admin — accounts only, not their data)</span></h2>
      {users.map((u) => (
        <div key={u.id} className="list-item row between">
          <span className="row" style={{ gap: 10 }}>
            <Avatar value={u.avatar} size={30} />
            <span>{u.name}{u.is_admin && <span className="muted small"> · admin</span>}
              {u.must_change_password && <span className="muted small"> · starter pw</span>}</span>
          </span>
          <span className="row" style={{ gap: 8 }}>
            <button className="btn ghost small" onClick={() => reset(u)}>reset pw</button>
            {u.id !== profile?.id && <button className="btn danger small" onClick={() => del(u)}>×</button>}
          </span>
        </div>
      ))}
      <div className="stack" style={{ marginTop: 14, borderTop: '1px solid var(--line)', paddingTop: 14 }}>
        <div className="row" style={{ gap: 8 }}>
          <Avatar value={nf.avatar} size={40} />
          <input type="text" placeholder="name" value={nf.name} onChange={(e) => setNf({ ...nf, name: e.target.value })} />
        </div>
        <div className="row" style={{ gap: 8 }}>
          <input type="text" placeholder="emoji (optional)" style={{ maxWidth: 150 }}
                 value={nf.avatar.startsWith('data:') ? '' : nf.avatar}
                 onChange={(e) => setNf({ ...nf, avatar: e.target.value })} />
          <label className="btn ghost small">upload photo
            <input type="file" accept="image/*" hidden onChange={uploadPhoto} /></label>
        </div>
        <input type="password" placeholder="initial password" value={nf.password} onChange={(e) => setNf({ ...nf, password: e.target.value })} />
        <label className="toggle small"><input type="checkbox" checked={nf.is_admin}
          onChange={(e) => setNf({ ...nf, is_admin: e.target.checked })} /><span>make admin</span></label>
        <button className="btn" onClick={add} disabled={!nf.name.trim() || !nf.password}>add profile</button>
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
