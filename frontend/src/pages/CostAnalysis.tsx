import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Loader2 } from 'lucide-react'

export const CostAnalysis: React.FC = () => {
  const [periodDays, setPeriodDays] = useState(30)

  const { data, isLoading, error } = useQuery({
    queryKey: ['cost-analysis', periodDays],
    queryFn: () => apiEndpoints.costAnalysis(periodDays).then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading cost analysis</div>
  }

  const summary = data.summary || {}
  const topIngredients = data.top_ingredients || []
  const spendingTrend = summary.spending_trend || []

  const projectedMonthly = (summary.avg_daily_spending || 0) * 30

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Cost Analysis</h1>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Period</CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <label className="text-sm font-medium mb-2 block">
              Period (Days): {periodDays}
            </label>
            <Slider
              min={7}
              max={365}
              step={1}
              value={periodDays}
              onChange={(e) => setPeriodDays(Number(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Total Spending"
          value={`$${summary.total_spending?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`}
        />
        <MetricCard
          title="Average Daily Spending"
          value={`$${summary.avg_daily_spending?.toFixed(2) || '0.00'}`}
        />
        <MetricCard
          title="Projected Monthly Spending"
          value={`$${projectedMonthly.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        />
      </div>

      {spendingTrend.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Spending Trend Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <PlotlyChart
              data={[
                {
                  x: spendingTrend.map((item: any) => item.date),
                  y: spendingTrend.map((item: any) => item.total_cost),
                  type: 'scatter',
                  mode: 'lines+markers',
                  line: { width: 2 },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Date' },
                yaxis: { title: 'Total Cost ($)' },
              }}
            />
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Ingredients by Cost</CardTitle>
          </CardHeader>
          <CardContent>
            {topIngredients.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    x: topIngredients.map((item: any) => item.value),
                    y: topIngredients.map((item: any) => item.ingredient),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: topIngredients.map((item: any) => item.value),
                      colorscale: 'Greens',
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Total Cost ($)' },
                  yaxis: { title: 'Ingredient' },
                }}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No cost data available
              </div>
            )}
          </CardContent>
        </Card>

        {summary.spending_by_supplier && Object.keys(summary.spending_by_supplier).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Spending by Supplier</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    values: Object.values(summary.spending_by_supplier),
                    labels: Object.keys(summary.spending_by_supplier),
                    type: 'pie',
                  },
                ]}
                layout={{
                  height: 400,
                }}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

