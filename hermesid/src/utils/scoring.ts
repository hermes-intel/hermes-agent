import type { ScoreResult, Dimension } from '../types'

function hashCode(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0x7fffffff
  }
  return hash
}

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const DIMENSION_DEFS: { name: string; nameZh: string }[] = [
  { name: 'AI Usage', nameZh: 'AI 使用' },
  { name: 'AI Understanding', nameZh: 'AI 理解' },
  { name: 'Communication', nameZh: '与他人沟通' },
  { name: 'Product Building', nameZh: '自己建设产品' },
  { name: 'Adoption Speed', nameZh: 'AI 采用速度' },
  { name: 'Prompt Engineering', nameZh: 'Prompt 精炼度' },
  { name: 'Critical Awareness', nameZh: 'AI 批判思维' },
  { name: 'Knowledge Sharing', nameZh: 'AI 知识分享' },
]

interface KnownProfile {
  totalScore: number
  level: string
  role: string
}

const KNOWN_HANDLES: Record<string, KnownProfile> = {
  teknium: { totalScore: 92, level: 'Agent God', role: 'Hermes Creator' },
  karpathy: { totalScore: 95, level: 'Agent God', role: 'AI Educator' },
  elonmusk: { totalScore: 78, level: 'AI Expert', role: 'Tech Visionary' },
  sama: { totalScore: 88, level: 'AI Native', role: 'AI Strategist' },
  ylecun: { totalScore: 94, level: 'Agent God', role: 'Neural Architect' },
  goodside: { totalScore: 90, level: 'AI Native', role: 'Prompt Whisperer' },
  emaborevol: { totalScore: 86, level: 'AI Native', role: 'Agent Builder' },
}

function getLevel(score: number): string {
  if (score >= 96) return 'Agent God'
  if (score >= 86) return 'AI Native'
  if (score >= 71) return 'AI Expert'
  if (score >= 51) return 'AI Practitioner'
  if (score >= 31) return 'AI Curious'
  return 'AI Newbie'
}

const ROLES = [
  'AI Enthusiast',
  'Prompt Whisperer',
  'Model Explorer',
  'AI Builder',
  'Tool Curator',
  'Agent Architect',
  'Data Alchemist',
  'AI Evangelist',
  'Tech Pioneer',
  'Digital Craftsman',
  'Neural Navigator',
  'AI Strategist',
  'Code Alchemist',
  'Pattern Seeker',
]

function generateSummary(
  handle: string,
  score: number,
  level: string,
): string {
  const pool: Record<string, string[]> = {
    'Agent God': [
      `@${handle} is at the pinnacle of AI mastery. A true Agent God.`,
      `Few reach this level. @${handle} doesn't just use AI — they shape it.`,
    ],
    'AI Native': [
      `@${handle} breathes AI. This is someone living in the future.`,
      `@${handle} has made AI an extension of their mind. Truly AI Native.`,
    ],
    'AI Expert': [
      `@${handle} has serious AI chops. Deep understanding meets practical skill.`,
      `@${handle} is well ahead of the curve — an AI Expert in every sense.`,
    ],
    'AI Practitioner': [
      `@${handle} is actively building with AI. On the path to mastery.`,
      `@${handle} knows the tools and uses them well. Keep pushing.`,
    ],
    'AI Curious': [
      `@${handle} is exploring the AI landscape. Curiosity is the first step.`,
      `@${handle} shows growing interest in AI. The best time to dive deeper is now.`,
    ],
    'AI Newbie': [
      `@${handle} is just getting started with AI. Every expert was once a beginner.`,
      `@${handle} has a world of AI to discover. The journey begins here.`,
    ],
  }
  const options = pool[level] || pool['AI Practitioner']
  return options[hashCode(handle + 'summary') % options.length]
}

export function generateScore(handle: string): ScoreResult {
  const clean = handle.replace(/^@/, '').toLowerCase().trim()
  const known = KNOWN_HANDLES[clean]
  const seed = hashCode(clean)
  const rand = mulberry32(seed)

  let dimensions: Dimension[]
  let totalScore: number

  if (known) {
    const target = known.totalScore
    dimensions = DIMENSION_DEFS.map((def) => {
      const variance = (rand() - 0.5) * 24
      const score = Math.max(
        45,
        Math.min(100, Math.round(target + variance)),
      )
      return { ...def, score }
    })
    totalScore = target
  } else {
    dimensions = DIMENSION_DEFS.map((def) => {
      const base = rand() * 50 + 45
      return { ...def, score: Math.round(base) }
    })
    totalScore = Math.round(
      dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length,
    )
  }

  const level = known?.level ?? getLevel(totalScore)
  const role =
    known?.role ?? ROLES[Math.floor(rand() * ROLES.length)]
  const summary = generateSummary(clean, totalScore, level)

  return { handle: clean, totalScore, level, role, dimensions, summary }
}
