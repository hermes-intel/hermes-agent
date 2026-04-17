import type { RefObject } from 'react'
import type { ScoreResult } from '../types'

interface Props {
  result: ScoreResult
  cardRef: RefObject<HTMLDivElement | null>
}

function hashCode(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0x7fffffff
  }
  return hash
}

function Avatar({ handle }: { handle: string }) {
  const h = hashCode(handle)
  const hue1 = h % 360
  const hue2 = (h * 13) % 360

  return (
    <div style={{ width: 170, height: 200, position: 'relative' }}>
      {/* Double border frame */}
      <svg
        viewBox="0 0 170 200"
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
      >
        <rect
          x="3"
          y="3"
          width="164"
          height="194"
          fill="none"
          stroke="#2B5CE6"
          strokeWidth="3"
          rx="3"
        />
        <rect
          x="9"
          y="9"
          width="152"
          height="182"
          fill="none"
          stroke="#2B5CE6"
          strokeWidth="1.5"
          rx="2"
        />
      </svg>

      {/* Avatar content */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          left: 12,
          right: 12,
          bottom: 12,
          overflow: 'hidden',
          background: `linear-gradient(135deg, hsl(${hue1},25%,22%), hsl(${hue2},30%,32%))`,
        }}
      >
        {/* Halftone pattern overlay */}
        <svg
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            opacity: 0.35,
          }}
        >
          <defs>
            <pattern
              id={`dots-${handle}`}
              width="5"
              height="5"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="2.5" cy="2.5" r="1.2" fill="white" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill={`url(#dots-${handle})`} />
        </svg>

        {/* Abstract figure silhouette */}
        <svg
          viewBox="0 0 100 130"
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            opacity: 0.6,
          }}
        >
          <circle cx="50" cy="38" r="20" fill="rgba(0,0,0,0.45)" />
          <ellipse cx="50" cy="42" rx="16" ry="12" fill="rgba(0,0,0,0.25)" />
          <path
            d="M25 130 Q25 75 50 68 Q75 75 75 130 Z"
            fill="rgba(0,0,0,0.35)"
          />
          {/* Hair spikes */}
          <path
            d={`M35 25 L30 8 L42 20 M50 22 L48 2 L55 18 M60 25 L68 6 L62 22 M42 28 L36 14 L46 24`}
            fill="none"
            stroke="rgba(0,0,0,0.4)"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>

        {/* Contrast/texture overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
          }}
        />
      </div>
    </div>
  )
}

function Barcode({ value }: { value: string }) {
  const h = hashCode(value)
  const bars: { x: number; w: number }[] = []
  let cursor = 0
  let hh = h

  for (let i = 0; i < 48; i++) {
    const bit = hh & 1
    const w = bit ? 2.8 : 1.4
    bars.push({ x: cursor, w })
    cursor += w + 1.2
    hh = hh >> 1
    if (hh === 0) hh = hashCode(value + String(i))
  }

  const totalW = cursor

  return (
    <svg viewBox={`0 0 ${totalW} 32`} style={{ width: 180, height: 28 }}>
      {bars.map((b, i) => (
        <rect key={i} x={b.x} y={0} width={b.w} height={32} fill="#111" />
      ))}
    </svg>
  )
}

function InfoRow({
  label,
  value,
  large,
}: {
  label: string
  value: string
  large?: boolean
}) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        padding: '3px 0',
      }}
    >
      <span
        style={{
          fontWeight: 700,
          fontSize: 16,
          color: '#111',
          fontFamily: "'Inter', sans-serif",
        }}
      >
        [{label}]
      </span>
      <span
        style={{
          fontWeight: large ? 800 : 600,
          fontSize: large ? 22 : 17,
          color: '#111',
          fontFamily: "'Inter', sans-serif",
        }}
      >
        {value}
      </span>
    </div>
  )
}

export default function ScoreCard({ result, cardRef }: Props) {
  const topDimensions = [...result.dimensions]
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)

  return (
    <div
      ref={cardRef}
      style={{
        width: 640,
        height: 880,
        background: '#2B5CE6',
        padding: '30px 30px 20px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* White card */}
      <div
        style={{
          width: 580,
          height: 780,
          background: 'white',
          borderRadius: 24,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          padding: '18px 28px 16px',
          boxSizing: 'border-box',
          position: 'relative',
        }}
      >
        {/* Top bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 11,
            color: '#999',
            marginBottom: 12,
          }}
        >
          <span>loading / hermes intel ai scorecard</span>
          <span style={{ color: '#2B5CE6', fontWeight: 600 }}>
            **Hermes Intel
          </span>
        </div>

        {/* Avatar + Title row */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 14 }}>
          <Avatar handle={result.handle} />

          <div style={{ flex: 1, paddingTop: 4 }}>
            <span
              style={{
                fontFamily: "'Permanent Marker', cursive",
                color: '#2B5CE6',
                fontSize: 28,
                lineHeight: 0.8,
              }}
            >
              {'\u275D '}
            </span>
            <div
              style={{
                fontFamily: "'Permanent Marker', cursive",
                color: '#2B5CE6',
                fontSize: 38,
                lineHeight: 1.05,
                letterSpacing: '-0.5px',
                marginTop: 2,
              }}
            >
              AI
              <br />
              IDENTIFICATION
              <br />
              CARD
            </div>
            <span
              style={{
                fontFamily: "'Permanent Marker', cursive",
                color: '#2B5CE6',
                fontSize: 28,
                lineHeight: 0.8,
                display: 'inline-block',
                marginTop: 4,
              }}
            >
              {' \u275E'}
            </span>
          </div>
        </div>

        {/* Info fields */}
        <div style={{ marginBottom: 8 }}>
          <InfoRow label="name" value={`@${result.handle}`} />
          <InfoRow
            label="AI Score"
            value={`${result.totalScore}/100`}
            large
          />
          <InfoRow label="Level" value={result.level} />
          <InfoRow label="Role*" value={result.role} />
        </div>

        {/* AI Proficiencies */}
        <div style={{ marginBottom: 8 }}>
          <p
            style={{
              fontWeight: 700,
              fontSize: 16,
              color: '#111',
              margin: '8px 0 6px',
              fontFamily: "'Inter', sans-serif",
            }}
          >
            [AI Proficiencies]
          </p>
          {topDimensions.map((d) => (
            <div
              key={d.name}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '3px 0 3px 12px',
                fontSize: 15,
                fontFamily: "'Inter', sans-serif",
              }}
            >
              <span style={{ color: '#333' }}>{d.name}</span>
              <span style={{ fontWeight: 700, color: '#111' }}>
                {d.score}
              </span>
            </div>
          ))}
        </div>

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Bottom section */}
        <div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-end',
              marginBottom: 8,
            }}
          >
            <span
              style={{
                fontFamily: "'Caveat', cursive",
                fontSize: 32,
                color: '#2B5CE6',
                fontWeight: 700,
                lineHeight: 1,
              }}
            >
              Hermes Agent
            </span>
            <Barcode value={result.handle} />
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: 11,
              color: '#888',
              borderTop: '1px solid #eee',
              paddingTop: 8,
            }}
          >
            <span>
              Powered by Hermes Agent &middot; Test your AI Native level
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="#888">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              @Hermes_Intel_
            </span>
          </div>
        </div>
      </div>

      {/* Footer outside card */}
      <p
        style={{
          color: 'white',
          textAlign: 'center',
          fontWeight: 700,
          fontSize: 20,
          marginTop: 16,
          letterSpacing: '0.5px',
          fontFamily: "'Inter', sans-serif",
        }}
      >
        hermesid.wtf
      </p>
    </div>
  )
}
