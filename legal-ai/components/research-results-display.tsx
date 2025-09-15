"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  FileText,
  Download,
  Copy,
  Share,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Calendar,
  Scale,
  BookOpen,
  Quote,
  BarChart3,
  Clock,
  CheckCircle,
  AlertTriangle,
} from "lucide-react"

interface CitedDocument {
  id: string
  title: string
  citation: string
  court: string
  date: string
  relevanceScore: number
  keyPassages: string[]
  url?: string
}

interface ResearchResult {
  success: boolean
  query: string
  timestamp: string | Date
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

interface ResearchResultsDisplayProps {
  result: ResearchResult | null
  isVisible: boolean
}

export function ResearchResultsDisplay({ result, isVisible }: ResearchResultsDisplayProps) {
  const [expandedDocuments, setExpandedDocuments] = useState<Set<string>>(new Set())
  const [copiedText, setCopiedText] = useState<string | null>(null)

  const toggleDocumentExpansion = (docId: string) => {
    const newExpanded = new Set(expandedDocuments)
    if (newExpanded.has(docId)) {
      newExpanded.delete(docId)
    } else {
      newExpanded.add(docId)
    }
    setExpandedDocuments(newExpanded)
  }

  const handleCopyText = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedText(label)
      setTimeout(() => setCopiedText(null), 2000)
    } catch (err) {
      console.error("Failed to copy text:", err)
    }
  }

  const handleExportResults = () => {
    if (!result) return

    const timestamp = new Date(result.timestamp)
    const exportData = {
      query: result.query,
      timestamp: timestamp.toISOString(),
      summary: result.executiveSummary,
      keyFindings: result.keyFindings,
      fullResponse: result.response,
      citedDocuments: result.citedDocuments,
      legalPrinciples: result.legalPrinciples,
      recommendations: result.recommendations,
      statistics: {
        documentsFound: result.documentsFound,
        uniqueDocuments: result.uniqueDocuments,
        relevantDocuments: result.relevantDocuments,
        processingTime: result.processingTime,
      },
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `legal-research-${timestamp.toISOString().split("T")[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (!isVisible || !result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Research Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Start a research query to see comprehensive results here</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!result.success) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            Research Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-600" />
            <p className="text-red-600 mb-2">Research failed to complete</p>
            <p className="text-sm text-muted-foreground">{result.error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Research Completed Successfully
              </CardTitle>
              <CardDescription className="text-base font-medium mb-3">"{result.query}"</CardDescription>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {new Date(result.timestamp).toLocaleString()}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {Math.round(result.processingTime)}s processing time
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => handleCopyText(result.response, "Full Response")}>
                <Copy className="h-4 w-4 mr-2" />
                {copiedText === "Full Response" ? "Copied!" : "Copy"}
              </Button>
              <Button variant="outline" size="sm" onClick={handleExportResults}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Share className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{result.documentsFound}</div>
              <div className="text-sm text-muted-foreground">Documents Found</div>
            </div>
            <div className="text-center p-3 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">{result.uniqueDocuments}</div>
              <div className="text-sm text-muted-foreground">Unique Documents</div>
            </div>
            <div className="text-center p-3 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{result.relevantDocuments}</div>
              <div className="text-sm text-muted-foreground">Relevant Documents</div>
            </div>
            <div className="text-center p-3 border rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{result.citedDocuments.length}</div>
              <div className="text-sm text-muted-foreground">Citations</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Results */}
      <Card>
        <CardContent className="p-0">
          <Tabs defaultValue="summary" className="w-full">
            <div className="px-6 pt-6">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="findings">Key Findings</TabsTrigger>
                <TabsTrigger value="full">Full Analysis</TabsTrigger>
                <TabsTrigger value="citations">Citations</TabsTrigger>
                <TabsTrigger value="principles">Legal Principles</TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="summary" className="px-6 pb-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Executive Summary
                  </h3>
                  <div className="prose prose-sm max-w-none">
                    <p className="text-foreground leading-relaxed">{result.executiveSummary}</p>
                  </div>
                </div>

                <Separator />

                <div>
                  <h4 className="font-medium mb-3">Recommendations</h4>
                  <ul className="space-y-2">
                    {result.recommendations.map((recommendation, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{recommendation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="findings" className="px-6 pb-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold mb-4">Key Research Findings</h3>
                <div className="space-y-3">
                  {result.keyFindings.map((finding, index) => (
                    <div key={index} className="p-4 border-l-4 border-primary bg-muted/50 rounded-r-lg">
                      <div className="flex items-start gap-3">
                        <Badge variant="outline" className="mt-0.5">
                          {index + 1}
                        </Badge>
                        <p className="text-sm leading-relaxed">{finding}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="full" className="px-6 pb-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Complete Legal Analysis</h3>
                  <Button variant="outline" size="sm" onClick={() => handleCopyText(result.response, "Full Analysis")}>
                    <Copy className="h-4 w-4 mr-2" />
                    {copiedText === "Full Analysis" ? "Copied!" : "Copy Text"}
                  </Button>
                </div>
                <ScrollArea className="h-96 border rounded-lg p-4">
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-foreground leading-relaxed">{result.response}</div>
                  </div>
                </ScrollArea>
              </div>
            </TabsContent>

            <TabsContent value="citations" className="px-6 pb-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold mb-4">Cited Legal Documents</h3>
                <div className="space-y-4">
                  {result.citedDocuments.map((doc) => (
                    <Collapsible key={doc.id}>
                      <div className="border rounded-lg">
                        <CollapsibleTrigger
                          className="w-full p-4 text-left hover:bg-muted/50 transition-colors"
                          onClick={() => toggleDocumentExpansion(doc.id)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="font-medium text-sm">{doc.title}</h4>
                                <Badge variant="outline" className="text-xs">
                                  {Math.round(doc.relevanceScore * 100)}% relevant
                                </Badge>
                              </div>
                              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                <span className="flex items-center gap-1">
                                  <Scale className="h-3 w-3" />
                                  {doc.court}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {doc.date}
                                </span>
                                <span className="font-mono">{doc.citation}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {doc.url && (
                                <Button variant="ghost" size="sm" asChild>
                                  <a href={doc.url} target="_blank" rel="noopener noreferrer">
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                </Button>
                              )}
                              {expandedDocuments.has(doc.id) ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </div>
                          </div>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <div className="px-4 pb-4 border-t bg-muted/25">
                            <h5 className="font-medium text-sm mb-3 mt-3 flex items-center gap-2">
                              <Quote className="h-4 w-4" />
                              Key Passages
                            </h5>
                            <div className="space-y-3">
                              {doc.keyPassages.map((passage, index) => (
                                <div key={index} className="p-3 bg-background border-l-2 border-primary rounded-r">
                                  <p className="text-sm italic leading-relaxed">"{passage}"</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        </CollapsibleContent>
                      </div>
                    </Collapsible>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="principles" className="px-6 pb-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Legal Principles Identified
                </h3>
                <div className="grid gap-3">
                  {result.legalPrinciples.map((principle, index) => (
                    <div key={index} className="p-4 border rounded-lg bg-card">
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">
                          {index + 1}
                        </div>
                        <p className="text-sm leading-relaxed">{principle}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
