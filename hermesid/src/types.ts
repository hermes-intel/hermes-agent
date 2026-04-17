export interface Dimension {
  name: string
  nameZh: string
  score: number
}

export interface ScoreResult {
  handle: string
  totalScore: number
  level: string
  role: string
  dimensions: Dimension[]
  summary: string
}
