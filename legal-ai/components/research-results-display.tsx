"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  FileText,
  Download,
  Copy,
  Share,
  ExternalLink,
  Calendar,
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
  link?: string  // Added for clickable links
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
  const [copiedText, setCopiedText] = useState<string | null>(null)
  const [processedMarkdown, setProcessedMarkdown] = useState<string>("")

  const handleCopyText = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedText(label)
      setTimeout(() => setCopiedText(null), 2000)
    } catch (err) {
      console.error("Failed to copy text:", err)
    }
  }

  // Process markdown to make file links clickable
  useEffect(() => {
    if (!result?.response) {
      setProcessedMarkdown("")
      return
    }

    let processedText = result.response

    // Create a mapping of cited documents for easy lookup
    const documentMap = new Map()
    result.citedDocuments?.forEach(doc => {
      documentMap.set(doc.title, doc)
      documentMap.set(doc.citation, doc)
      // Also map common variations
      const shortName = doc.title.replace(/^R\. v\. /, "").replace(/, \d{4} \w+ \d+.*$/, "")
      documentMap.set(shortName, doc)
    })

    // Replace document mentions with clickable links
    // Look for patterns like "R. v. [Name]" or document titles
    processedText = processedText.replace(
      /\b(R\. v\. [A-Z][a-zA-Z\s,.']+(?:\d{4} \w+ \d+)?)\b/g,
      (match) => {
        const doc = documentMap.get(match) || 
                   documentMap.get(match.replace(/, \d{4} \w+ \d+.*$/, "")) ||
                   Array.from(documentMap.values()).find(d => 
                     match.includes(d.title.replace(/^R\. v\. /, "").replace(/, \d{4} \w+ \d+.*$/, ""))
                   )
        
        if (doc?.link || doc?.url) {
          return `[${match}](${doc.link || doc.url})`
        }
        return match
      }
    )

    // Remove asterisks around case citations that might have been added for emphasis
    processedText = processedText.replace(
      /\*(\bR\. v\. [A-Z][a-zA-Z\s,.']+(?:\d{4} \w+ \d+)?)\*/g,
      '$1'
    )

    setProcessedMarkdown(processedText)
  }, [result])

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
            <p className="text-sm text-muted-foreground">{result.error || "An unexpected error occurred"}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderMarkdownWithLinks = (text: string) => {
    // Split text into lines for better processing
    const lines = text.split('\n')
    
    return lines.map((line, lineIndex) => {
      // Handle headers
      if (line.startsWith('#')) {
        const level = line.match(/^#+/)?.[0].length || 1
        const headerText = line.replace(/^#+\s*/, '')
        const HeaderTag = `h${Math.min(level, 6)}` as keyof JSX.IntrinsicElements
        return (
          <HeaderTag key={lineIndex} className={`font-bold mt-4 mb-2 ${
            level === 1 ? 'text-2xl' : 
            level === 2 ? 'text-xl' : 
            level === 3 ? 'text-lg' : 
            'text-base'
          }`}>
            {headerText}
          </HeaderTag>
        )
      }
      
      // Handle bullet points
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const bulletText = line.replace(/^[-*]\s*/, '')
        return (
          <div key={lineIndex} className="flex items-start gap-2 mb-1">
            <span className="text-blue-600 mt-1">•</span>
            <span>{renderInlineMarkdown(bulletText)}</span>
          </div>
        )
      }
      
      // Handle regular paragraphs
      if (line.trim()) {
        return (
          <p key={lineIndex} className="mb-2">
            {renderInlineMarkdown(line)}
          </p>
        )
      }
      
      // Empty lines
      return <br key={lineIndex} />
    })
  }

  const renderInlineMarkdown = (text: string) => {
    // First handle links, then bold text
    const parts = []
    let remaining = text
    
    // Process links first
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g
    let lastIndex = 0
    let match
    
    while ((match = linkRegex.exec(text)) !== null) {
      // Add text before the link
      if (match.index > lastIndex) {
        const beforeText = text.slice(lastIndex, match.index)
        parts.push(renderBoldText(beforeText))
      }
      
      // Add the link
      const linkText = match[1]
      const url = match[2]
      parts.push(
        <a
          key={match.index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
        >
          {linkText}
          <ExternalLink className="h-3 w-3" />
        </a>
      )
      
      lastIndex = match.index + match[0].length
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      const remainingText = text.slice(lastIndex)
      parts.push(renderBoldText(remainingText))
    }
    
    return parts.length > 0 ? parts : renderBoldText(text)
  }

  const renderBoldText = (text: string) => {
    // Handle bold text with **text** or *text*
    const boldRegex = /\*\*([^*]+)\*\*|\*([^*]+)\*/g
    const parts = []
    let lastIndex = 0
    let match
    
    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before the bold
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index))
      }
      
      // Add the bold text
      const boldText = match[1] || match[2]
      parts.push(
        <strong key={match.index} className="font-bold">
          {boldText}
        </strong>
      )
      
      lastIndex = match.index + match[0].length
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex))
    }
    
    return parts.length > 0 ? parts : text
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

      {/* Markdown Results Display */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Legal Research Analysis
          </CardTitle>
          <CardDescription>
            Complete analysis with clickable case references
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] w-full border rounded-lg p-6">
            <div className="prose prose-sm max-w-none">
              <div className="whitespace-pre-wrap text-foreground leading-relaxed">
                {renderMarkdownWithLinks(processedMarkdown || result.response)}
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
