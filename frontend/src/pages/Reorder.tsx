import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/DataTable'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'

export const Reorder: React.FC = () => {
  const [includeSeasonality, setIncludeSeasonality] = useState(true)
  const [urgencyFilter, setUrgencyFilter] = useState<string[]>(['Critical', 'High', 'Medium', 'Low'])

  const { data, isLoading, error } = useQuery({
    queryKey: ['reorder', includeSeasonality],
    queryFn: () => apiEndpoints.reorder(includeSeasonality).then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading reorder recommendations</div>
  }

  const recommendations = data.data || []
  const summary = data.summary || {}

  const filteredRecommendations = recommendations.filter((item: any) =>
    urgencyFilter.includes(item.urgency)
  )

  // Always show all urgency levels, even if some don't have items

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Reorder Recommendations</h1>

      <Card>
        <CardHeader>
          <CardTitle>Options</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeSeasonality}
              onChange={(e) => setIncludeSeasonality(e.target.checked)}
            />
            <span className="text-sm">Include Seasonality in Recommendations</span>
          </label>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Critical"
          value={summary.critical || 0}
          delta={summary.critical > 0 ? '⚠️ Urgent' : undefined}
          deltaType={summary.critical > 0 ? 'decrease' : 'neutral'}
        />
        <MetricCard title="High" value={summary.high || 0} />
        <MetricCard title="Medium" value={summary.medium || 0} />
        <MetricCard
          title="Total Recommended Order"
          value={summary.total_recommended_order?.toFixed(0) || '0'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filter by Urgency</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {['Critical', 'High', 'Medium', 'Low'].map((urgency: string) => {
              const count = recommendations.filter((item: any) => item.urgency === urgency).length
              return (
                <button
                  key={urgency}
                  onClick={() => {
                    if (urgencyFilter.includes(urgency)) {
                      setUrgencyFilter(urgencyFilter.filter((u) => u !== urgency))
                    } else {
                      setUrgencyFilter([...urgencyFilter, urgency])
                    }
                  }}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    urgencyFilter.includes(urgency)
                      ? 'bg-primary text-white'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                  title={`${count} items with ${urgency} urgency`}
                >
                  {urgency} {count > 0 && `(${count})`}
                </button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <DataTable
        data={filteredRecommendations}
        columns={[
          { key: 'ingredient', label: 'Ingredient', sortable: true },
          {
            key: 'current_stock',
            label: 'Current Stock',
            sortable: true,
            render: value => Number(value).toFixed(2),
          },
          {
            key: 'min_stock_level',
            label: 'Min Stock Level',
            sortable: true,
          },
          {
            key: 'days_until_stockout',
            label: 'Days Until Stockout',
            sortable: true,
            render: value => Math.round(Number(value)),
          },
          {
            key: 'forecasted_demand_30d',
            label: 'Forecasted Demand (30d)',
            sortable: true,
            render: value => Number(value).toFixed(2),
          },
          {
            key: 'recommended_order_quantity',
            label: 'Recommended Order Qty',
            sortable: true,
            render: value => Number(value).toFixed(2),
          },
          {
            key: 'urgency',
            label: 'Urgency',
            sortable: true,
            render: value => (
              <Badge
                variant={
                  value === 'Critical'
                    ? 'destructive'
                    : value === 'High'
                    ? 'secondary'
                    : 'default'
                }
              >
                {value}
              </Badge>
            ),
          },
          {
            key: 'estimated_lead_time_days',
            label: 'Lead Time (Days)',
            sortable: true,
            render: value => Math.round(Number(value)),
          },
          {
            key: 'reorder_date',
            label: 'Recommended Reorder Date',
            sortable: true,
          },
        ]}
        title="Detailed Reorder Recommendations"
        searchable
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recommended Order Quantities</CardTitle>
          </CardHeader>
          <CardContent>
            {filteredRecommendations.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    x: filteredRecommendations
                      .slice(0, 15)
                      .map((item: any) => item.recommended_order_quantity),
                    y: filteredRecommendations
                      .slice(0, 15)
                      .map((item: any) => item.ingredient),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: filteredRecommendations.slice(0, 15).map((item: any) =>
                        item.urgency === 'Critical'
                          ? 'red'
                          : item.urgency === 'High'
                          ? 'orange'
                          : item.urgency === 'Medium'
                          ? 'yellow'
                          : 'green'
                      ),
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Recommended Order Quantity' },
                  yaxis: { title: 'Ingredient' },
                }}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No recommendations available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Urgency Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {filteredRecommendations.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    values: Object.values(
                      filteredRecommendations.reduce((acc: any, item: any) => {
                        acc[item.urgency] = (acc[item.urgency] || 0) + 1
                        return acc
                      }, {})
                    ),
                    labels: Object.keys(
                      filteredRecommendations.reduce((acc: any, item: any) => {
                        acc[item.urgency] = (acc[item.urgency] || 0) + 1
                        return acc
                      }, {})
                    ),
                    type: 'pie',
                    marker: {
                      colors: ['red', 'orange', 'yellow', 'green'],
                    },
                  },
                ]}
                layout={{
                  height: 400,
                }}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

