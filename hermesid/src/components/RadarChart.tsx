import type { Dimension } from '../types'

interface Props {
  dimensions: Dimension[]
  size?: number
  strokeColor?: string
  fillColor?: string
  labelColor?: string
}

export default function RadarChart({
  dimensions,
  size = 300,
  strokeColor = '#2B5CE6',
  fillColor = 'rgba(43,92,230,0.25)',
  labelColor = 'white',
}: Props) {
  const center = size / 2
  const radius = size / 2 - 50
  const n = dimensions.length

  const getPoint = (
    index: number,
    value: number,
  ): [number, number] => {
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2
    const r = (value / 100) * radius
    return [
      center + r * Math.cos(angle),
      center + r * Math.sin(angle),
    ]
  }

  const gridLevels = [20, 40, 60, 80, 100]

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-xs mx-auto">
      {gridLevels.map((level) => (
        <polygon
          key={level}
          points={Array.from({ length: n }, (_, i) =>
            getPoint(i, level).join(','),
          ).join(' ')}
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth="1"
        />
      ))}

      {Array.from({ length: n }, (_, i) => {
        const [x, y] = getPoint(i, 100)
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={x}
            y2={y}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
          />
        )
      })}

      <polygon
        points={dimensions
          .map((d, i) => getPoint(i, d.score).join(','))
          .join(' ')}
        fill={fillColor}
        stroke={strokeColor}
        strokeWidth="2.5"
      />

      {dimensions.map((d, i) => {
        const [x, y] = getPoint(i, d.score)
        return (
          <circle
            key={`dot-${i}`}
            cx={x}
            cy={y}
            r="4"
            fill={strokeColor}
          />
        )
      })}

      {dimensions.map((d, i) => {
        const [x, y] = getPoint(i, 120)
        return (
          <text
            key={`label-${i}`}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={labelColor}
            fontSize="9"
            fontWeight="500"
            fontFamily="Inter, system-ui, sans-serif"
          >
            {d.name}
          </text>
        )
      })}
    </svg>
  )
}
