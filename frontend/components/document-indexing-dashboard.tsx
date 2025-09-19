"use client"

import { useState, useEffect } from "react"
import { useSystemStatus, useDocuments, api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Database,
  FileText,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Upload,
  Trash2,
  Eye,
  Clock,
  HardDrive,
  Loader2,
} from "lucide-react"

export function DocumentIndexingDashboard() {
  const { status: systemStatus, loading: statusLoading, refresh: refreshStatus } = useSystemStatus()
  const { documents, loading: documentsLoading, refresh: refreshDocuments } = useDocuments()
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexingProgress, setIndexingProgress] = useState(0)

  // Simulate indexing progress (in real implementation, this would come from WebSocket)
  const handleRebuildIndex = async () => {
    try {
      setIsIndexing(true)
      setIndexingProgress(0)
      
      await api.startIndexing(true)
      
      // Simulate progress updates
      const interval = setInterval(() => {
        setIndexingProgress(prev => {
          const newProgress = prev + 10
          if (newProgress >= 100) {
            clearInterval(interval)
            setIsIndexing(false)
            refreshStatus()
            refreshDocuments()
            return 100
          }
          return newProgress
        })
      }, 500)
      
    } catch (error) {
      console.error('Failed to start indexing:', error)
      setIsIndexing(false)
      alert('Failed to start indexing. Please try again.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "indexed":
        return "default"
      case "processing":
        return "secondary"
      case "error":
        return "destructive"
      case "pending":
        return "outline"
      default:
        return "outline"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "indexed":
        return <CheckCircle className="h-3 w-3" />
      case "processing":
        return <RefreshCw className="h-3 w-3 animate-spin" />
      case "error":
        return <AlertCircle className="h-3 w-3" />
      case "pending":
        return <Clock className="h-3 w-3" />
      default:
        return <Clock className="h-3 w-3" />
    }
  }

  if (statusLoading || documentsLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mr-2" />
              <span>Loading document index...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Index Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Document Index Statistics
          </CardTitle>
          <CardDescription>Overview of your legal document database</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-primary">{systemStatus?.documentCount || 0}</div>
              <div className="text-sm text-muted-foreground">Total Files</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">{systemStatus?.indexStats.filesProcessed || 0}</div>
              <div className="text-sm text-muted-foreground">Indexed Files</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{systemStatus?.indexStats.chunksIndexed || 0}</div>
              <div className="text-sm text-muted-foreground">Text Chunks</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {systemStatus?.vectorDbStats ? 
                  `${Math.round((systemStatus.indexStats.chunksIndexed * 384 * 4) / (1024 * 1024))} MB` : 
                  'N/A'
                }
              </div>
              <div className="text-sm text-muted-foreground">Index Size</div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HardDrive className="h-4 w-4" />
                <span className="text-sm font-medium">Index Status</span>
              </div>
              <Badge variant={isIndexing ? "secondary" : systemStatus?.indexingCompleted ? "default" : "destructive"}>
                {isIndexing ? "Indexing..." : systemStatus?.indexingCompleted ? "Ready" : "Not Ready"}
              </Badge>
            </div>

            {isIndexing && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Indexing Progress</span>
                  <span>{indexingProgress}%</span>
                </div>
                <Progress value={indexingProgress} />
              </div>
            )}

            <div className="flex items-center justify-between text-sm">
              <span>Vector Database</span>
              <span className="text-muted-foreground">
                {systemStatus?.vectorDbStats ? 'Connected' : 'Not Available'}
              </span>
            </div>

            <Separator />

            <div className="flex gap-2">
              <Button 
                onClick={handleRebuildIndex} 
                disabled={isIndexing} 
                variant="outline" 
                size="sm"
              >
                {isIndexing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Rebuilding...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Rebuild Index
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm" disabled>
                <Upload className="h-4 w-4 mr-2" />
                Add Documents
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Legal Document Library
          </CardTitle>
          <CardDescription>Manage and monitor your indexed legal documents</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-3">
              {documents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No documents found</p>
                  <p className="text-sm">Add legal case files to the assets/decisions directory</p>
                </div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-start gap-3 flex-1">
                      <FileText className="h-5 w-5 mt-0.5 text-muted-foreground" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-sm truncate">{doc.name}</h4>
                          <Badge variant={getStatusColor(doc.status)} className="text-xs">
                            {getStatusIcon(doc.status)}
                            <span className="ml-1 capitalize">{doc.status}</span>
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{doc.type}</span>
                          <span>{doc.size} MB</span>
                          {doc.status === "indexed" && doc.chunks > 0 && (
                            <span>{doc.chunks} chunks</span>
                          )}
                          <span>Modified {new Date(doc.lastModified).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" disabled>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" disabled>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}