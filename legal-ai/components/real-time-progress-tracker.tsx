"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Clock,
  Search,
  Filter,
  BookOpen,
  Brain,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  BarChart3,
  Zap,
  Database,
  Eye,
} from "lucide-react"

interface DocumentStatus {
  name: string
  status: "pending" | "reading" | "completed" | "error"
  chunks: number
  relevantChunks: number
  processingTime: number
}

interface StageProgress {
  stage: "retrieval" | "pruning" | "reading" | "aggregation" | "completed" | "idle"
  status: string
  currentActivity: string
  elapsedTime: number
  progress: number
  documentsFound?: number
  documentsBeingRead?: DocumentStatus[]
  completedReadings?: number
  totalReadings?: number
  stageStartTime?: number
  stageDurations?: Record<string, number>
  stageElapsedTime?: number
}

interface RealTimeProgressTrackerProps {
  isActive: boolean
  progress?: any // Progress data from API
  onComplete?: () => void
}

export function RealTimeProgressTracker({ isActive, progress: apiProgress, onComplete }: RealTimeProgressTrackerProps) {
  const [progress, setProgress] = useState<StageProgress>({
    stage: "idle",
    status: "Ready to research",
    currentActivity: "Waiting for query",
    elapsedTime: 0,
    progress: 0,
  })

  const [stageHistory, setStageHistory] = useState<
    Array<{
      stage: string
      duration: number
      status: "completed" | "active" | "pending"
    }>
  >([])

  // Use real progress data from API
  useEffect(() => {
    if (!isActive) {
      setProgress({
        stage: "idle",
        status: "Ready to research",
        currentActivity: "Waiting for query",
        elapsedTime: 0,
        progress: 0,
      })
      setStageHistory([])
      return
    }

    // If we have API progress data, use it
    if (apiProgress) {
      setProgress({
        stage: apiProgress.stage || "idle",
        status: apiProgress.status || "Processing",
        currentActivity: apiProgress.currentActivity || "",
        elapsedTime: apiProgress.elapsedTime || 0,
        progress: apiProgress.progress || 0,
        documentsFound: apiProgress.documentsFound,
        documentsBeingRead: apiProgress.documentsBeingRead,
        completedReadings: apiProgress.completedReadings,
        totalReadings: apiProgress.totalReadings,
        stageDurations: apiProgress.stageDurations,
        stageElapsedTime: apiProgress.stageElapsedTime,
      })

      // Update stage history based on current stage and actual durations
      const allStages = ["retrieval", "pruning", "reading", "aggregation"]
      const currentStageIndex = allStages.indexOf(apiProgress.stage)
      const stageDurations = apiProgress.stageDurations || {}
      
      setStageHistory((prev) => {
        const newHistory = allStages.map((stage, index) => {
          let duration = 0
          let status: "completed" | "active" | "pending" = "pending"
          
          if (index < currentStageIndex) {
            // Completed stage - use actual duration from progress tracker
            duration = stageDurations[stage] || 0
            status = "completed"
          } else if (index === currentStageIndex) {
            // Current stage - use stage elapsed time
            duration = apiProgress.stageElapsedTime || 0
            status = "active"
          }
          
          return {
            stage,
            duration: Math.round(duration),
            status
          }
        })
        return newHistory
      })

      // Check if completed
      if (apiProgress.stage === "completed" || apiProgress.progress >= 100) {
        setStageHistory((prev) => prev.map((s) => ({ ...s, status: "completed" as const })))
        onComplete?.()
      }
    }
  }, [isActive, apiProgress, onComplete])

  const getStageIcon = (stage: string, status: "completed" | "active" | "pending") => {
    const iconProps = { className: "h-4 w-4" }

    if (status === "completed") return <CheckCircle {...iconProps} className="h-4 w-4 text-green-600" />
    if (status === "active") return <RefreshCw {...iconProps} className="h-4 w-4 text-blue-600 animate-spin" />

    switch (stage) {
      case "retrieval":
        return <Search {...iconProps} className="h-4 w-4 text-muted-foreground" />
      case "pruning":
        return <Filter {...iconProps} className="h-4 w-4 text-muted-foreground" />
      case "reading":
        return <BookOpen {...iconProps} className="h-4 w-4 text-muted-foreground" />
      case "aggregation":
        return <Brain {...iconProps} className="h-4 w-4 text-muted-foreground" />
      default:
        return <Clock {...iconProps} className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getDocumentStatusIcon = (status: DocumentStatus["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-3 w-3 text-green-600" />
      case "reading":
        return <RefreshCw className="h-3 w-3 text-blue-600 animate-spin" />
      case "error":
        return <AlertCircle className="h-3 w-3 text-red-600" />
      default:
        return <Clock className="h-3 w-3 text-muted-foreground" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Main Progress Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Research Progress
          </CardTitle>
          <CardDescription>Real-time tracking of AI research process</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Progress */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span className="text-sm font-medium">Status:</span>
                <span className="text-sm">{progress.status}</span>
              </div>
              <div className="flex items-center gap-4">
                <Badge variant="outline" className="flex items-center gap-1">
                  <Zap className="h-3 w-3" />
                  {progress.elapsedTime}s elapsed
                </Badge>
                {progress.documentsFound && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Database className="h-3 w-3" />
                    {progress.documentsFound} docs found
                  </Badge>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Current Activity</span>
                <span className="text-muted-foreground">{progress.currentActivity}</span>
              </div>
              <Progress value={progress.progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0%</span>
                <span>{Math.round(progress.progress)}% complete</span>
                <span>100%</span>
              </div>
            </div>
          </div>

          <Separator />

          {/* Stage Progress */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Processing Stages</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {["Retrieval", "Pruning", "Reading", "Aggregation"].map((stageName, index) => {
                const stageKey = stageName.toLowerCase()
                const stageInfo = stageHistory.find((s) => s.stage === stageKey)
                const isActive = progress.stage === stageKey
                const isCompleted = stageInfo?.status === "completed"
                const isPending = !isActive && !isCompleted

                return (
                  <div
                    key={stageName}
                    className={`p-3 border rounded-lg ${isActive ? "border-blue-500 bg-blue-50" : isCompleted ? "border-green-500 bg-green-50" : "border-gray-200"}`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {getStageIcon(stageKey, isCompleted ? "completed" : isActive ? "active" : "pending")}
                      <span
                        className={`text-sm font-medium ${isActive ? "text-blue-700" : isCompleted ? "text-green-700" : "text-muted-foreground"}`}
                      >
                        {stageName}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {isCompleted && stageInfo ? `${stageInfo.duration}s` : isActive ? "In progress..." : "Pending"}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Document Reading Progress - Show all files being read in parallel */}
      {progress.stage === "reading" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Document Reading Progress
            </CardTitle>
            <CardDescription>
              Reading {progress.completedReadings || 0}/{progress.totalReadings || 0} documents in parallel
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {progress.documentsBeingRead && progress.documentsBeingRead.map((doc, index) => (
                  <div 
                    key={index} 
                    className={`p-3 border rounded-lg transition-all duration-300 ${
                      doc.status === "completed" 
                        ? "border-green-500 bg-green-50" 
                        : doc.status === "reading" 
                        ? "border-blue-500 bg-blue-50" 
                        : doc.status === "error"
                        ? "border-red-500 bg-red-50"
                        : "border-gray-200"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="flex-shrink-0 mt-0.5">
                        {doc.status === "completed" ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : doc.status === "reading" ? (
                          <div className="relative">
                            <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                            <div className="absolute inset-0 rounded-full border-2 border-blue-200 border-t-blue-600 animate-pulse"></div>
                          </div>
                        ) : doc.status === "error" ? (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        ) : (
                          <Clock className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1 mb-1">
                          <span className="font-medium text-xs truncate" title={doc.name}>
                            {doc.name}
                          </span>
                        </div>
                        
                        <div className="space-y-1">
                          <Badge 
                            variant="outline" 
                            className={`text-xs capitalize ${
                              doc.status === "completed" 
                                ? "bg-green-100 text-green-700 border-green-300"
                                : doc.status === "reading"
                                ? "bg-blue-100 text-blue-700 border-blue-300"
                                : doc.status === "error"
                                ? "bg-red-100 text-red-700 border-red-300"
                                : ""
                            }`}
                          >
                            {doc.status === "completed" ? "✓ Complete" : 
                             doc.status === "reading" ? "● Reading..." :
                             doc.status === "error" ? "✗ Error" : "⋯ Pending"}
                          </Badge>
                          
                          {doc.status === "reading" && (
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div 
                                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300 animate-pulse" 
                                style={{ width: "60%" }}
                              ></div>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{doc.chunks || 0} chunks</span>
                            {doc.relevantChunks > 0 && (
                              <span className="text-green-600">• {doc.relevantChunks} relevant</span>
                            )}
                            {doc.processingTime > 0 && (
                              <span>• {doc.processingTime}s</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Show placeholder cards if no documents data available yet */}
                {(!progress.documentsBeingRead || progress.documentsBeingRead.length === 0) && (
                  Array.from({ length: Math.min(progress.totalReadings || 6, 12) }).map((_, index) => (
                    <div key={index} className="p-3 border rounded-lg border-gray-200 animate-pulse">
                      <div className="flex items-start gap-2">
                        <div className="flex-shrink-0 mt-0.5">
                          <div className="h-4 w-4 bg-gray-200 rounded-full animate-pulse"></div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="h-3 bg-gray-200 rounded mb-2 animate-pulse"></div>
                          <div className="h-2 bg-gray-100 rounded animate-pulse"></div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
            
            {/* Progress Summary */}
            {progress.documentsBeingRead && progress.documentsBeingRead.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Reading Progress</span>
                  <span className="font-medium">
                    {Math.round(((progress.completedReadings || 0) / (progress.totalReadings || 1)) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-500" 
                    style={{ 
                      width: `${Math.round(((progress.completedReadings || 0) / (progress.totalReadings || 1)) * 100)}%` 
                    }}
                  ></div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Performance Metrics */}
      {progress.stage !== "idle" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 border rounded-lg">
                <div className="text-lg font-bold text-blue-600">{progress.elapsedTime}s</div>
                <div className="text-xs text-muted-foreground">Total Time</div>
              </div>
              <div className="text-center p-3 border rounded-lg">
                <div className="text-lg font-bold text-green-600">{progress.documentsFound || 0}</div>
                <div className="text-xs text-muted-foreground">Documents Found</div>
              </div>
              <div className="text-center p-3 border rounded-lg">
                <div className="text-lg font-bold text-purple-600">{progress.completedReadings || 0}</div>
                <div className="text-xs text-muted-foreground">Documents Read</div>
              </div>
              <div className="text-center p-3 border rounded-lg">
                <div className="text-lg font-bold text-orange-600">{Math.round(progress.progress)}%</div>
                <div className="text-xs text-muted-foreground">Progress</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
