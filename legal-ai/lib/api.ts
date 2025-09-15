import { useState, useEffect, useCallback } from 'react'

// API Base URL - update this to match your FastAPI server
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Type definitions
export interface SystemStatus {
  indexingCompleted: boolean
  documentCount: number
  indexStats: {
    filesProcessed: number
    chunksIndexed: number
  }
  vectorDbStats?: any
}

export interface DocumentInfo {
  id: string
  name: string
  type: string
  size: number
  status: 'indexed' | 'processing' | 'error' | 'pending'
  chunks: number
  lastModified: string
}

export interface ResearchProgress {
  stage: 'retrieval' | 'pruning' | 'reading' | 'aggregation' | 'completed' | 'idle'
  status: string
  currentActivity: string
  elapsedTime: number
  progress: number
  documentsFound?: number
  documentsBeingRead?: any[]
  completedReadings?: number
  totalReadings?: number
}

export interface CitedDocument {
  id: string
  title: string
  citation: string
  court: string
  date: string
  relevanceScore: number
  keyPassages: string[]
  url?: string
}

export interface ResearchResult {
  success: boolean
  query: string
  timestamp: string
  documentsFound: number
  uniqueDocuments: number
  relevantDocuments: number
  response: string
  executiveSummary: string
  keyFindings: string[]
  citedDocuments: CitedDocument[]
  legalPrinciples: string[]
  recommendations: string[]
  processingTime: number
  error?: string
}

// API Functions
export const api = {
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${API_BASE_URL}/api/status`)
    if (!response.ok) throw new Error('Failed to get system status')
    return response.json()
  },

  async getDocuments(): Promise<DocumentInfo[]> {
    const response = await fetch(`${API_BASE_URL}/api/documents`)
    if (!response.ok) throw new Error('Failed to get documents')
    return response.json()
  },

  async startIndexing(rebuild: boolean = false): Promise<{ session_id: string }> {
    const response = await fetch(`${API_BASE_URL}/api/indexing/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rebuild })
    })
    if (!response.ok) throw new Error('Failed to start indexing')
    return response.json()
  },

  async startResearch(query: string, filters?: any): Promise<{ session_id: string }> {
    const response = await fetch(`${API_BASE_URL}/api/research/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, filters })
    })
    if (!response.ok) throw new Error('Failed to start research')
    return response.json()
  },

  async getResearchProgress(sessionId: string): Promise<ResearchProgress> {
    const response = await fetch(`${API_BASE_URL}/api/research/progress/${sessionId}`)
    if (!response.ok) throw new Error('Failed to get research progress')
    return response.json()
  },

  async getResearchResults(sessionId: string): Promise<ResearchResult> {
    const response = await fetch(`${API_BASE_URL}/api/research/results/${sessionId}`)
    if (!response.ok) {
      if (response.status === 202) {
        throw new Error('RESEARCH_NOT_COMPLETE')
      }
      throw new Error('Failed to get research results')
    }
    return response.json()
  }
}

// Custom Hooks
export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getSystemStatus()
      setStatus(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { status, loading, error, refresh }
}

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getDocuments()
      setDocuments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { documents, loading, error, refresh }
}

export function useResearchProgress(sessionId: string | null) {
  const [progress, setProgress] = useState<ResearchProgress | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      setProgress(null)
      return
    }

    let ws: WebSocket | null = null
    let pollInterval: NodeJS.Timeout | null = null

    const connectWebSocket = () => {
      try {
        const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/progress/${sessionId}`
        ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket connected for session:', sessionId)
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            setProgress(data)
            setError(null)
          } catch (err) {
            console.error('Error parsing WebSocket message:', err)
          }
        }
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          // Fallback to polling if WebSocket fails
          startPolling()
        }
        
        ws.onclose = () => {
          console.log('WebSocket closed')
          // Try to reconnect if not intentionally closed
          if (sessionId) {
            setTimeout(connectWebSocket, 2000)
          }
        }
      } catch (err) {
        console.error('Failed to connect WebSocket:', err)
        startPolling()
      }
    }

    const startPolling = () => {
      if (pollInterval) clearInterval(pollInterval)
      
      pollInterval = setInterval(async () => {
        try {
          const data = await api.getResearchProgress(sessionId)
          setProgress(data)
          setError(null)
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Unknown error')
        }
      }, 1000)
    }

    // Try WebSocket first, fallback to polling
    connectWebSocket()

    return () => {
      if (ws) {
        ws.close()
        ws = null
      }
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }
  }, [sessionId])

  return { progress, loading, error }
}

export function useResearchResults(sessionId: string | null) {
  const [result, setResult] = useState<ResearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchResults = useCallback(async () => {
    if (!sessionId) return

    try {
      setLoading(true)
      setError(null)
      const data = await api.getResearchResults(sessionId)
      setResult(data)
    } catch (err) {
      if (err instanceof Error && err.message === 'RESEARCH_NOT_COMPLETE') {
        // Research not complete yet, this is expected
        return
      }
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    if (sessionId) {
      fetchResults()
    } else {
      setResult(null)
    }
  }, [sessionId, fetchResults])

  return { result, loading, error, refresh: fetchResults }
}
