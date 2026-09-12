const TERMS = [
  ['fund', 'A bucket for one kind of spending — Rent, Food, Hobbies. Every expense goes into exactly one fund.'],
  ['budget', "How much you plan to spend from a fund in a month. Each fund has a default amount that repeats every month; you can override it for one month when something's different."],
  ['label', "A sticky note on an expense — food, friend, trip-goa. Put as many as you like. Labels cut across funds, so you can ask 'how much on dining out?' even though it's spread over Food and Outings."],
  ['group', 'A saved bunch of labels, so you can filter by them in one tap.'],
  ['spent', 'What you actually spent from a fund this month.'],
  ['left', "What's still unspent — budget minus spent. Shown in green."],
  ['exceeded', 'How much you went over budget. Shown in red.'],
  ['siphoned', "Moving spare budget from one fund to cover another that went over. If Hobbies has money to spare and Food is over, you siphon from Hobbies into Food. Shown in blue — tap the fund to see where it came from."],
  ['carried over', "At month-end you can carry a fund's result into next month. Two flavours: if you underspent, the leftover rolls forward and next month has a bit more. If you overspent, next month is trimmed to make up for it (you can spread that over a few months, EMI-style). Off by default — you switch it on per fund."],
  ['close the month', "The button that applies carry-over. Until you close a month, nothing rolls forward. It's safe to run again — it just recalculates."],
]

export default function Terms() {
  return (
    <div className="card">
      <h1 style={{ marginBottom: 6 }}>the words, simply</h1>
      <p className="muted" style={{ marginTop: 0 }}>khata in plain terms — no finance-speak.</p>
      <dl className="terms">
        {TERMS.map(([term, desc]) => (
          <div key={term} className="list-item">
            <dt><b>{term}</b></dt>
            <dd className="muted" style={{ margin: '4px 0 0' }}>{desc}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
