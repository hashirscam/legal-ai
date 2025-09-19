"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Search,
  BookOpen,
  FileText,
  Play,
  RefreshCw,
  Settings,
  Filter,
  Clock,
  Calendar,
  MapPin,
  Scale,
} from "lucide-react"

interface QueryFilters {
  dateRange: string
  jurisdiction: string
  caseType: string[]
  includeUnpublished: boolean
  maxResults: number
}

interface SavedQuery {
  id: string
  name: string
  query: string
  filters: QueryFilters
  lastUsed: Date
  resultCount: number
}

interface ResearchQueryInterfaceProps {
  currentQuery: string
  setCurrentQuery: (query: string) => void
  onStartResearch: () => void
  isResearching: boolean
}

export function ResearchQueryInterface({
  currentQuery,
  setCurrentQuery,
  onStartResearch,
  isResearching,
}: ResearchQueryInterfaceProps) {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [filters, setFilters] = useState<QueryFilters>({
    dateRange: "all",
    jurisdiction: "ontario",
    caseType: ["criminal"],
    includeUnpublished: false,
    maxResults: 50,
  })

  const [savedQueries] = useState<SavedQuery[]>([
    {
      id: "1",
      name: "Ontario Sexual Assault Cases 2025",
      query: "Sexual assault cases with publication bans in Ontario 2025",
      filters: {
        dateRange: "2025",
        jurisdiction: "ontario",
        caseType: ["criminal"],
        includeUnpublished: false,
        maxResults: 50,
      },
      lastUsed: new Date(Date.now() - 86400000),
      resultCount: 12,
    },
    {
      id: "2",
      name: "Child Protection Sentencing",
      query: "Sentencing guidelines for internet-based sexual offences involving minors",
      filters: {
        dateRange: "last-5-years",
        jurisdiction: "canada",
        caseType: ["criminal", "family"],
        includeUnpublished: true,
        maxResults: 100,
      },
      lastUsed: new Date(Date.now() - 172800000),
      resultCount: 28,
    },
  ])

  const exampleQueries = [
    {
      category: "Criminal Law",
      queries: [
        "Criminal cases involving pedophiles in Ontario 2025",
        "Sexual assault cases with publication bans",
        "Recent decisions on child pornography charges",
        "Cases involving breach of trust by public officials",
      ],
    },
    {
      category: "Sentencing",
      queries: [
        "Sentencing guidelines for internet-based sexual offences",
        "Conditional sentences for sexual assault cases",
        "Aggravating factors in child exploitation cases",
        "Precedents for minimum sentences in sexual offences",
      ],
    },
    {
      category: "Procedural",
      queries: [
        "Publication ban applications in sexual assault cases",
        "Victim impact statements in sentencing decisions",
        "Expert testimony in child abuse cases",
        "Admissibility of digital evidence in sexual offence cases",
      ],
    },
  ]

  const handleFilterChange = (key: keyof QueryFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const handleCaseTypeChange = (caseType: string, checked: boolean) => {
    setFilters((prev) => ({
      ...prev,
      caseType: checked ? [...prev.caseType, caseType] : prev.caseType.filter((type) => type !== caseType),
    }))
  }

  const loadSavedQuery = (savedQuery: SavedQuery) => {
    setCurrentQuery(savedQuery.query)
    setFilters(savedQuery.filters)
  }

  return (
    <div className="space-y-6">
      {/* Main Query Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Legal Research Query
          </CardTitle>
          <CardDescription>
            Enter your legal research question to get comprehensive, AI-powered analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Research Question</Label>
            <Textarea
              id="query"
              placeholder="Enter your legal research query here... (e.g., 'Recent Ontario cases involving sexual assault with publication bans')"
              value={currentQuery}
              onChange={(e) => setCurrentQuery(e.target.value)}
              className="min-h-32 resize-none"
            />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>{currentQuery.length} characters</span>
                <span>•</span>
                <span>Estimated {Math.ceil(currentQuery.split(" ").length / 10)} search terms</span>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}>
                  <Filter className="h-4 w-4 mr-2" />
                  {showAdvancedFilters ? "Hide" : "Show"} Filters
                </Button>
                <Button
                  onClick={onStartResearch}
                  disabled={!currentQuery.trim() || isResearching}
                  className="bg-primary hover:bg-primary/90"
                >
                  {isResearching ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Researching...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" /> Start Research
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Advanced Filters */}
          {showAdvancedFilters && (
            <>
              <Separator />
              <div className="space-y-4">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Advanced Search Filters
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="dateRange">Date Range</Label>
                    <Select value={filters.dateRange} onValueChange={(value) => handleFilterChange("dateRange", value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Time</SelectItem>
                        <SelectItem value="2025">2025</SelectItem>
                        <SelectItem value="2024">2024</SelectItem>
                        <SelectItem value="last-year">Last Year</SelectItem>
                        <SelectItem value="last-5-years">Last 5 Years</SelectItem>
                        <SelectItem value="last-10-years">Last 10 Years</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="jurisdiction">Jurisdiction</Label>
                    <Select
                      value={filters.jurisdiction}
                      onValueChange={(value) => handleFilterChange("jurisdiction", value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="canada">All Canada</SelectItem>
                        <SelectItem value="ontario">Ontario</SelectItem>
                        <SelectItem value="quebec">Quebec</SelectItem>
                        <SelectItem value="bc">British Columbia</SelectItem>
                        <SelectItem value="alberta">Alberta</SelectItem>
                        <SelectItem value="federal">Federal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="maxResults">Max Results</Label>
                    <Input
                      id="maxResults"
                      type="number"
                      min="10"
                      max="200"
                      value={filters.maxResults}
                      onChange={(e) => handleFilterChange("maxResults", Number.parseInt(e.target.value))}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Case Types</Label>
                  <div className="flex flex-wrap gap-4">
                    {["criminal", "civil", "family", "administrative", "constitutional"].map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={type}
                          checked={filters.caseType.includes(type)}
                          onCheckedChange={(checked) => handleCaseTypeChange(type, checked as boolean)}
                        />
                        <Label htmlFor={type} className="text-sm capitalize">
                          {type}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="unpublished"
                    checked={filters.includeUnpublished}
                    onCheckedChange={(checked) => handleFilterChange("includeUnpublished", checked)}
                  />
                  <Label htmlFor="unpublished" className="text-sm">
                    Include unpublished decisions
                  </Label>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Example Queries */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Example Queries
            </CardTitle>
            <CardDescription>Click any example to use as your starting point</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80">
              <div className="space-y-4">
                {exampleQueries.map((category, categoryIndex) => (
                  <div key={categoryIndex} className="space-y-2">
                    <h4 className="text-sm font-medium text-primary flex items-center gap-2">
                      <Scale className="h-3 w-3" />
                      {category.category}
                    </h4>
                    <div className="space-y-1">
                      {category.queries.map((query, queryIndex) => (
                        <Button
                          key={queryIndex}
                          variant="ghost"
                          size="sm"
                          className="justify-start text-left h-auto p-2 whitespace-normal w-full"
                          onClick={() => setCurrentQuery(query)}
                        >
                          <FileText className="h-3 w-3 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-xs">{query}</span>
                        </Button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Saved Queries */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Saved Queries
            </CardTitle>
            <CardDescription>Your frequently used research queries</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80">
              <div className="space-y-3">
                {savedQueries.map((savedQuery) => (
                  <div key={savedQuery.id} className="p-3 border rounded-lg space-y-2">
                    <div className="flex items-start justify-between">
                      <h4 className="font-medium text-sm">{savedQuery.name}</h4>
                      <Badge variant="outline" className="text-xs">
                        {savedQuery.resultCount} results
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">{savedQuery.query}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        <span>{savedQuery.lastUsed.toLocaleDateString()}</span>
                        <MapPin className="h-3 w-3 ml-2" />
                        <span className="capitalize">{savedQuery.filters.jurisdiction}</span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => loadSavedQuery(savedQuery)}
                        className="text-xs"
                      >
                        Load Query
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
