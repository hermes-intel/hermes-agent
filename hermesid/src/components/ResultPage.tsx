import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toPng } from 'html-to-image'
import { generateScore } from '../utils/scoring'
import type { ScoreResult } from '../types'
import ScoreCard from './ScoreCard'
import RadarChart from './RadarChart'

export default function ResultPage() {
  const { handle } = useParams<{ handle: string }>()
  const [result, setResult] = useState<ScoreResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    setLoading(true)
    setResult(null)
    const timer = setTimeout(() => {
      setResult(generateScore(handle ?? ''))
      setLoading(false)
    }, 2200)
    return () => clearTimeout(timer)
  }, [handle])

  const handleDownload = async () => {
    if (!cardRef.current || downloading) return
    setDownloading(true)
    try {
      const dataUrl = await toPng(cardRef.current, {
        pixelRatio: 2,
        cacheBust: true,
      })
      const link = document.createElement('a')
      link.download = `hermes-id-${handle}.png`
      link.href = dataUrl
      link.click()
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setDownloading(false)
    }
  }

  const handleShareX = () => {
    if (!result) return
    const text = `My AI Score is ${result.totalScore}/100 — Level: ${result.level}!\n\nTest your AI Native level at hermesid.wtf\n\n@Hermes_Intel_`
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`
    window.open(url, '_blank')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#2B5CE6] flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div
            className="animate-spin-slow mx-auto mb-5"
            style={{
              width: 48,
              height: 48,
              border: '4px solid rgba(255,255,255,0.2)',
              borderTopColor: 'white',
              borderRadius: '50%',
            }}
          />
          <p className="text-white text-xl font-semibold">
            Analyzing @{handle}...
          </p>
          <p className="text-white/50 mt-2 text-sm">
            Hermes is reading your AI footprint
          </p>
        </div>
      </div>
    )
  }

  if (!result) return null

  return (
    <div className="min-h-screen bg-[#2B5CE6] flex flex-col items-center py-8 px-4">
      {/* The card — rendered on screen and used for export */}
      <div className="animate-fade-in-up">
        <div
          style={{
            transform: 'scale(0.85)',
            transformOrigin: 'top center',
          }}
          className="max-[700px]:!scale-[0.55] max-[700px]:!origin-top"
        >
          <ScoreCard result={result} cardRef={cardRef} />
        </div>
      </div>

      {/* Summary */}
      <p
        className="text-white/80 text-center max-w-md text-base mt-2 animate-fade-in-up delay-100"
        style={{ fontStyle: 'italic' }}
      >
        {result.summary}
      </p>

      {/* Action buttons */}
      <div className="flex gap-4 mt-6 animate-fade-in-up delay-200">
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-[#2B5CE6] font-semibold hover:bg-gray-50 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          {downloading ? 'Saving...' : 'Download Card'}
        </button>
        <button
          onClick={handleShareX}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gray-900 text-white font-semibold hover:bg-gray-800 active:scale-95 transition-all cursor-pointer"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
          Share to X
        </button>
      </div>

      {/* Detailed breakdown */}
      <div className="w-full max-w-md mt-10 animate-fade-in-up delay-300">
        <h3 className="text-white font-bold text-xl mb-4 text-center">
          Full AI Profile
        </h3>

        <div className="mb-6">
          <RadarChart dimensions={result.dimensions} />
        </div>

        <div className="space-y-3">
          {result.dimensions.map((d) => (
            <div key={d.name} className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex justify-between text-sm text-white mb-1">
                  <span className="font-medium">{d.name}</span>
                  <span className="font-bold">{d.score}</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${d.score}%`,
                      background:
                        'linear-gradient(90deg, #5B8AFF, #2B5CE6)',
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Test another */}
      <button
        onClick={() => navigate('/')}
        className="mt-10 mb-6 text-white/50 hover:text-white/80 underline underline-offset-4 text-sm transition-colors cursor-pointer"
      >
        Test another handle
      </button>
    </div>
  )
}
