"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DocumentIndexingDashboard } from "@/components/document-indexing-dashboard"
import { ResearchQueryInterface } from "@/components/research-query-interface"
import { RealTimeProgressTracker } from "@/components/real-time-progress-tracker"
import { ResearchResultsDisplay } from "@/components/research-results-display"
import { Scale, Search, Database, CheckCircle, AlertCircle, RefreshCw, History, Loader2 } from "lucide-react"
import { useSystemStatus, useResearchProgress, useResearchResults, api, ResearchResult } from "@/lib/api"

export default function LegalAIResearchSystem() {
  const [currentQuery, setCurrentQuery] = useState("")
  const [isResearching, setIsResearching] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [researchHistory, setResearchHistory] = useState<ResearchResult[]>([])
  const [currentView, setCurrentView] = useState<"research" | "indexing">("research")

  // Use API hooks
  const { status: systemStatus, loading: statusLoading, error: statusError, refresh: refreshStatus } = useSystemStatus()
  const { progress } = useResearchProgress(currentSessionId)
  const { result: currentResult, refresh: refreshResults } = useResearchResults(currentSessionId)

  // Add result to history when research completes
  useEffect(() => {
    if (currentResult && currentResult.success) {
      setResearchHistory(prev => {
        // Avoid duplicates
        const exists = prev.some(r => 
          r.query === currentResult.query && 
          Math.abs(new Date(r.timestamp).getTime() - new Date(currentResult.timestamp).getTime()) < 1000
        )
        
        if (!exists) {
          return [currentResult, ...prev.slice(0, 9)] // Keep last 10
        }
        return prev
      })
    }
  }, [currentResult])

  // Handle research completion
  useEffect(() => {
    if (progress && (progress.stage === "completed" || progress.progress >= 100)) {
      setIsResearching(false)
      // Try to fetch results
      if (currentSessionId) {
        setTimeout(() => refreshResults(), 1000)
      }
    }
  }, [progress, currentSessionId, refreshResults])

  const handleStartResearch = async () => {
    if (!currentQuery.trim()) return
    
    try {
    setIsResearching(true)
      const response = await api.startResearch(currentQuery)
      setCurrentSessionId(response.session_id)
    } catch (error) {
      console.error('Failed to start research:', error)
      setIsResearching(false)
      // Show error to user
      alert('Failed to start research. Please try again.')
    }
  }

  const handleRebuildIndex = async () => {
    try {
      await api.startIndexing(true)
      // Refresh status after a delay
      setTimeout(() => refreshStatus(), 2000)
    } catch (error) {
      console.error('Failed to rebuild index:', error)
      alert('Failed to rebuild index. Please try again.')
    }
  }

  if (statusLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading Legal AI Research System...</p>
        </div>
      </div>
    )
  }

  if (statusError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to connect to backend</p>
          <p className="text-muted-foreground mb-4">{statusError}</p>
          <Button onClick={refreshStatus}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-primary text-primary-foreground">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Scale className="h-8 w-8" />
              <div>
                <h1 className="text-2xl font-bold">Legal AI Research System</h1>
                <p className="text-primary-foreground/80">AI-powered case law research and analysis</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={currentView === "research" ? "secondary" : "ghost"}
                onClick={() => setCurrentView("research")}
                className="text-primary-foreground hover:text-primary-foreground"
              >
                <Search className="h-4 w-4 mr-2" />
                Research
              </Button>
              <Button
                variant={currentView === "indexing" ? "secondary" : "ghost"}
                onClick={() => setCurrentView("indexing")}
                className="text-primary-foreground hover:text-primary-foreground"
              >
                <Database className="h-4 w-4 mr-2" />
                Document Index
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-6">
        {currentView === "indexing" ? (
          <DocumentIndexingDashboard />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              {/* System Status */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    System Status
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Index Status</span>
                    <Badge variant={systemStatus?.indexingCompleted ? "default" : "secondary"}>
                      {systemStatus?.indexingCompleted ? (
                        <>
                          <CheckCircle className="h-3 w-3 mr-1" /> Ready
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-3 w-3 mr-1" /> Not Ready
                        </>
                      )}
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Documents</span>
                      <span className="font-medium">{systemStatus?.documentCount || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Files Processed</span>
                      <span className="font-medium">{systemStatus?.indexStats.filesProcessed || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Chunks Indexed</span>
                      <span className="font-medium">{systemStatus?.indexStats.chunksIndexed || 0}</span>
                    </div>
                  </div>

                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full bg-transparent"
                    onClick={handleRebuildIndex}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Rebuild Index
                  </Button>
                </CardContent>
              </Card>

              {/* Research History */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                    Research History
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-48">
                    <div className="space-y-3">
                      {researchHistory.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          No research history yet
                        </p>
                      ) : (
                        researchHistory.map((result, index) => (
                        <div
                          key={index}
                          className="p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                            onClick={() => {
                              // You could implement switching to view historical results here
                            }}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <Badge variant={result.success ? "default" : "destructive"} className="text-xs">
                              {result.success ? "Success" : "Error"}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                                {new Date(result.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-sm font-medium line-clamp-2 mb-2">{result.query}</p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{result.documentsFound} docs</span>
                            <span>{result.relevantDocuments} relevant</span>
                          </div>
                        </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 space-y-6">
              {/* Research Query Interface */}
              <ResearchQueryInterface
                currentQuery={currentQuery}
                setCurrentQuery={setCurrentQuery}
                onStartResearch={handleStartResearch}
                isResearching={isResearching}
              />

              {/* Progress Tracking */}
              <RealTimeProgressTracker 
                isActive={isResearching} 
                progress={progress}
                onComplete={() => setIsResearching(false)} 
              />

              {/* Results Display */}
              <ResearchResultsDisplay 
                result={currentResult} 
                isVisible={!isResearching} 
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}