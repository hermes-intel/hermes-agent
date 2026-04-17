import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const [handle, setHandle] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const clean = handle.replace(/^@/, '').trim()
    if (clean) navigate(`/score/${clean}`)
  }

  return (
    <div className="min-h-screen bg-[#2B5CE6] flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Floating card silhouettes */}
        <div
          className="absolute animate-float"
          style={{
            top: '8%',
            right: '6%',
            width: 180,
            height: 240,
            background: 'rgba(255,255,255,0.04)',
            borderRadius: 16,
            transform: 'rotate(12deg)',
          }}
        />
        <div
          className="absolute animate-float"
          style={{
            bottom: '12%',
            left: '5%',
            width: 140,
            height: 190,
            background: 'rgba(255,255,255,0.03)',
            borderRadius: 14,
            transform: 'rotate(-8deg)',
            animationDelay: '2s',
          }}
        />
        <div
          className="absolute animate-float"
          style={{
            top: '35%',
            left: '10%',
            width: 100,
            height: 135,
            background: 'rgba(255,255,255,0.025)',
            borderRadius: 12,
            transform: 'rotate(5deg)',
            animationDelay: '4s',
          }}
        />
        {/* Glow */}
        <div
          className="absolute"
          style={{
            top: '30%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 600,
            height: 600,
            borderRadius: '50%',
            background:
              'radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%)',
          }}
        />
      </div>

      {/* Main content */}
      <div className="relative z-10 text-center max-w-md w-full">
        {/* Logo area */}
        <p
          className="text-white/70 text-sm tracking-widest uppercase mb-3 animate-fade-in"
          style={{ fontFamily: "'Inter', sans-serif" }}
        >
          Powered by
        </p>
        <h2
          className="text-white text-4xl mb-6 animate-fade-in delay-100"
          style={{ fontFamily: "'Caveat', cursive", fontWeight: 700 }}
        >
          Hermes Agent
        </h2>

        {/* Title */}
        <h1
          className="text-white mb-4 animate-fade-in-up delay-100"
          style={{
            fontFamily: "'Permanent Marker', cursive",
            fontSize: 'clamp(2.2rem, 8vw, 3.5rem)',
            lineHeight: 1.1,
            letterSpacing: '-0.5px',
          }}
        >
          AI IDENTIFICATION
          <br />
          CARD
        </h1>

        <p className="text-white/75 text-lg mb-10 animate-fade-in-up delay-200">
          Test your AI Native level
        </p>

        {/* Input form */}
        <form
          onSubmit={handleSubmit}
          className="space-y-4 animate-fade-in-up delay-300"
        >
          <div className="relative">
            <span className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 text-xl font-semibold select-none">
              @
            </span>
            <input
              type="text"
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              placeholder="Enter your X handle"
              className="w-full py-4 pl-12 pr-5 rounded-2xl bg-white text-gray-800 text-lg placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-white/25 transition-shadow"
              autoFocus
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <button
            type="submit"
            disabled={!handle.replace(/^@/, '').trim()}
            className="w-full py-4 rounded-2xl bg-gray-900 text-white text-lg font-semibold hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer active:scale-[0.98]"
          >
            Generate My AI Score
          </button>
        </form>

        {/* Tagline */}
        <p className="text-white/40 text-sm mt-10 animate-fade-in delay-400">
          hermesid.wtf &middot; free &middot; no login required
        </p>
      </div>
    </div>
  )
}
