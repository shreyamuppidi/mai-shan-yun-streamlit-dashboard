import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { DataTable } from '@/components/DataTable'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle2 } from 'lucide-react'

export const RiskAlerts: React.FC = () => {
  const [riskTypeFilter, setRiskTypeFilter] = useState<string[]>([])
  const [reorderedItems, setReorderedItems] = useState<Set<string>>(new Set())
  const [showSuccessMessage, setShowSuccessMessage] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['risk-alerts'],
    queryFn: () => apiEndpoints.riskAlerts().then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading risk alerts</div>
  }

  const riskAlerts = data.data || []
  const summary = data.summary || {}

  const uniqueRiskTypes = Array.from(new Set(riskAlerts.map((item: any) => item.risk_type))) as string[]

  const filteredAlerts = riskTypeFilter.length > 0
    ? riskAlerts.filter((item: any) => riskTypeFilter.includes(item.risk_type))
    : riskAlerts

  const sortedAlerts = [...filteredAlerts].sort((a: any, b: any) => b.risk_score - a.risk_score)

  const handleReorder = (ingredient: string) => {
    // Add to reordered items set
    setReorderedItems((prev) => new Set([...prev, ingredient]))
    
    // Show success message
    setShowSuccessMessage(ingredient)
    
    // Hide success message after 3 seconds
    setTimeout(() => {
      setShowSuccessMessage(null)
    }, 3000)
    
    // In a real application, you would make an API call here:
    // apiEndpoints.reorderItem(ingredient).then(...)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Real-Time Inventory Risk Alerts</h1>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="High Risk Items"
          value={summary.high_risk_items || 0}
          delta={summary.high_risk_items > 0 ? '⚠️' : undefined}
          deltaType={summary.high_risk_items > 0 ? 'decrease' : 'neutral'}
        />
        <MetricCard
          title="Needs Reorder"
          value={summary.needs_reorder || 0}
          delta={summary.needs_reorder > 0 ? 'Urgent' : undefined}
          deltaType={summary.needs_reorder > 0 ? 'decrease' : 'neutral'}
        />
        <MetricCard
          title="Overstocked Items"
          value={summary.overstocked_items || 0}
        />
        <MetricCard
          title="Average Risk Score"
          value={summary.avg_risk_score ? summary.avg_risk_score.toFixed(1) : '0'}
        />
      </div>

      {/* Risk Type Filter */}
      {uniqueRiskTypes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Filter by Risk Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {uniqueRiskTypes.map((type: string) => (
                <button
                  key={String(type)}
                  onClick={() => {
                    if (riskTypeFilter.includes(type)) {
                      setRiskTypeFilter(riskTypeFilter.filter((t) => t !== type))
                    } else {
                      setRiskTypeFilter([...riskTypeFilter, type])
                    }
                  }}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    riskTypeFilter.includes(type)
                      ? 'bg-primary text-white'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  {String(type)}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risk Alerts Table */}
      <DataTable
        data={sortedAlerts}
        columns={[
          { key: 'ingredient', label: 'Ingredient', sortable: true },
          {
            key: 'current_stock',
            label: 'Current Stock',
            sortable: true,
            render: (value) => Number(value).toFixed(2),
          },
          {
            key: 'min_stock_level',
            label: 'Min Level',
            sortable: true,
          },
          {
            key: 'max_stock_level',
            label: 'Max Level',
            sortable: true,
          },
          {
            key: 'usage_velocity_7d',
            label: 'Usage Velocity (7d)',
            sortable: true,
            render: (value) => Number(value).toFixed(2),
          },
          {
            key: 'days_until_stockout',
            label: 'Days Until Stockout',
            sortable: true,
            render: (value) => Math.round(Number(value)),
          },
          {
            key: 'risk_score',
            label: 'Risk Score',
            sortable: true,
            render: (value) => (
              <Badge variant={Number(value) >= 50 ? 'destructive' : 'default'}>
                {Math.round(Number(value))}
              </Badge>
            ),
          },
          {
            key: 'risk_type',
            label: 'Risk Type',
            sortable: true,
          },
          {
            key: 'needs_reorder',
            label: 'Needs Reorder',
            sortable: true,
            render: (value) => (value ? 'Yes' : 'No'),
          },
        ]}
        title="Risk Alerts Details"
        searchable
      />

      {/* Success Message */}
      {showSuccessMessage && (
        <Alert className="bg-green-500/20 border-green-500/50 flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-green-400 flex-shrink-0" />
          <AlertDescription className="text-green-400 m-0">
            Reorder request sent for <strong>{showSuccessMessage}</strong>
          </AlertDescription>
        </Alert>
      )}

      {/* Critical Items */}
      {sortedAlerts.filter((item: any) => item.needs_reorder).length > 0 && (
        <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-red-500/30 shadow-xl">
          <CardHeader className="border-b border-white/10">
            <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-1 h-6 bg-gradient-to-b from-red-400 to-orange-500 rounded-full" />
              🚨 Critical Items - Reorder Now
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            {sortedAlerts
              .filter((item: any) => item.needs_reorder)
              .slice(0, 5)
              .map((item: any) => {
                const isReordered = reorderedItems.has(item.ingredient)
                return (
                  <div
                    key={item.ingredient}
                    className={`flex items-center justify-between p-4 rounded-lg border-2 transition-all duration-200 ${
                      isReordered
                        ? 'bg-green-500/10 border-green-500/50'
                        : 'bg-white/5 border-white/10 hover:border-red-500/30 hover:bg-white/10'
                    }`}
                  >
                    <div className="flex-1">
                      <h3 className="font-semibold text-white mb-1">{item.ingredient}</h3>
                      <p className="text-sm text-white/70">
                        Risk Score: {Math.round(item.risk_score)} - {item.risk_type}
                      </p>
                      <p className="text-sm text-white/70">
                        Days until stockout: {Math.round(item.days_until_stockout)}
                      </p>
                    </div>
                    <Button
                      variant={isReordered ? "default" : "destructive"}
                      onClick={() => handleReorder(item.ingredient)}
                      disabled={isReordered}
                      className="ml-4 min-w-[120px]"
                    >
                      {isReordered ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Reordered
                        </>
                      ) : (
                        'Reorder Now'
                      )}
                    </Button>
                  </div>
                )
              })}
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Risk Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <PlotlyChart
              data={[
                {
                  x: sortedAlerts.map((item: any) => item.risk_score),
                  type: 'histogram',
                  nbinsx: 20,
                  marker: { color: 'rgb(220, 38, 38)' },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Risk Score' },
                yaxis: { title: 'Number of Ingredients' },
              }}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Risk Items</CardTitle>
          </CardHeader>
          <CardContent>
            <PlotlyChart
              data={[
                {
                  x: sortedAlerts.slice(0, 10).map((item: any) => item.risk_score),
                  y: sortedAlerts.slice(0, 10).map((item: any) => item.ingredient),
                  type: 'bar',
                  orientation: 'h',
                  marker: {
                    color: sortedAlerts.slice(0, 10).map((item: any) => item.risk_score),
                    colorscale: 'Reds',
                  },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Risk Score' },
                yaxis: { title: 'Ingredient' },
              }}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

