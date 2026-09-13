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

// Avatar: renders an <img> for an uploaded data: URI, else the emoji text.
export function Avatar({ value, size = 28 }) {
  const s = {
    width: size, height: size, borderRadius: '50%', display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center', fontSize: Math.round(size * 0.6),
    background: 'var(--accent-soft)', overflow: 'hidden', flex: '0 0 auto',
  }
  if (value && value.startsWith('data:')) {
    return <span style={s}><img src={value} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /></span>
  }
  return <span style={s}>{value || '🙂'}</span>
}

// Downscale an uploaded image to a small square-ish JPEG data URI (kept tiny for the DB).
export function fileToAvatarDataURL(file, max = 128) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    const img = new Image()
    reader.onerror = reject
    reader.onload = () => { img.src = reader.result }
    img.onerror = reject
    img.onload = () => {
      const scale = Math.min(1, max / Math.max(img.width, img.height))
      const w = Math.round(img.width * scale)
      const h = Math.round(img.height * scale)
      const canvas = document.createElement('canvas')
      canvas.width = w; canvas.height = h
      canvas.getContext('2d').drawImage(img, 0, 0, w, h)
      resolve(canvas.toDataURL('image/jpeg', 0.82))
    }
    reader.readAsDataURL(file)
  })
}

// Modal to crop an uploaded image to a square (shown with a circular guide),
// with drag-to-pan and a zoom slider. Emits a small JPEG data URI.
export function AvatarCropper({ file, onDone, onCancel, size = 260, out = 128 }) {
  const [url, setUrl] = useState(null)
  const [nat, setNat] = useState(null)
  const [zoom, setZoom] = useState(1)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const drag = useRef(null)

  useEffect(() => {
    const r = new FileReader()
    r.onload = () => setUrl(r.result)
    r.readAsDataURL(file)
  }, [file])

  const base = nat ? size / Math.min(nat.w, nat.h) : 1
  const dispW = nat ? nat.w * base * zoom : 0
  const dispH = nat ? nat.h * base * zoom : 0

  const clamp = (p) => ({
    x: Math.min(0, Math.max(size - dispW, p.x)),
    y: Math.min(0, Math.max(size - dispH, p.y)),
  })
  useEffect(() => { if (nat) setPos((p) => clamp(p)) }, [zoom, nat])

  function onDown(e) {
    drag.current = { px: e.clientX, py: e.clientY, ox: pos.x, oy: pos.y }
    e.currentTarget.setPointerCapture(e.pointerId)
  }
  function onMove(e) {
    if (!drag.current) return
    setPos(clamp({ x: drag.current.ox + (e.clientX - drag.current.px), y: drag.current.oy + (e.clientY - drag.current.py) }))
  }
  function onUp() { drag.current = null }

  function confirm() {
    const scale = base * zoom
    const sSize = size / scale
    const canvas = document.createElement('canvas')
    canvas.width = out; canvas.height = out
    const ctx = canvas.getContext('2d')
    const img = new Image()
    img.onload = () => {
      ctx.drawImage(img, -pos.x / scale, -pos.y / scale, sSize, sSize, 0, 0, out, out)
      onDone(canvas.toDataURL('image/jpeg', 0.85))
    }
    img.src = url
  }

  return (
    <div className="modal-backdrop" onMouseDown={onCancel}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <h2>crop photo</h2>
        <div className="crop-view" style={{ width: size, height: size }}
             onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp}>
          {url && (
            <img src={url} draggable={false}
                 onLoad={(e) => { setNat({ w: e.target.naturalWidth, h: e.target.naturalHeight }); setZoom(1); setPos({ x: 0, y: 0 }) }}
                 style={{ width: dispW || 'auto', height: dispH || 'auto', left: pos.x, top: pos.y }} />
          )}
          <div className="crop-ring" />
        </div>
        <input type="range" min="1" max="3" step="0.01" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} />
        <div className="row" style={{ gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
          <button className="btn ghost" onClick={onCancel}>cancel</button>
          <button className="btn" onClick={confirm} disabled={!nat}>use photo</button>
        </div>
      </div>
    </div>
  )
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
