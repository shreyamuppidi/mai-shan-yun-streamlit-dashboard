import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

export const UsageTrends: React.FC = () => {
  const [selectedIngredient, setSelectedIngredient] = useState<string>('All')
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('monthly')

  // Fetch available ingredients
  const { data: ingredientsData } = useQuery({
    queryKey: ['ingredients'],
    queryFn: () => apiEndpoints.ingredients().then((res) => res.data),
  })

  const ingredients = ingredientsData?.ingredients || []

  const { data, isLoading, error } = useQuery({
    queryKey: ['usage-trends', selectedIngredient, period],
    queryFn: () =>
      apiEndpoints
        .usageTrends(selectedIngredient === 'All' ? undefined : selectedIngredient, period)
        .then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading usage trends</div>
  }

  const trends = data.trends || []
  const topIngredients = data.top_ingredients || []

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Usage Trends</h1>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm">Ingredient:</label>
            <Select
              value={selectedIngredient}
              onChange={(e) => setSelectedIngredient(e.target.value)}
              className="w-48"
            >
              <option value="All">All</option>
              {ingredients.map((ingredient: string) => (
                <option key={ingredient} value={ingredient}>
                  {ingredient}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Period:</label>
            <Select
              value={period}
              onChange={(e) => setPeriod(e.target.value as 'daily' | 'weekly' | 'monthly')}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Usage Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Usage Trends ({period.charAt(0).toUpperCase() + period.slice(1)})</CardTitle>
        </CardHeader>
        <CardContent>
          {trends.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: trends.map((item: any) => String(item.period || item.date || '')),
                  y: trends.map((item: any) => Number(item.quantity_used || item.value || 0)),
                  type: 'scatter',
                  mode: 'lines+markers',
                  line: { width: 2 },
                  marker: { size: 6 },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Period' },
                yaxis: { title: 'Quantity Used' },
              }}
              animationDelay={0.1}
            />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No trend data available for the selected criteria
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Ingredients */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Ingredients by Usage (Last 30 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            {topIngredients.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    x: topIngredients.map((item: any) => Number(item.value || item.quantity_used || 0)),
                    y: topIngredients.map((item: any) => String(item.ingredient || '')),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: topIngredients.map((item: any) => Number(item.value || item.quantity_used || 0)),
                      colorscale: 'Blues',
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Usage' },
                  yaxis: { title: 'Ingredient', categoryorder: 'total ascending' },
                }}
                animationDelay={0.2}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No usage data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Usage Distribution by Ingredient</CardTitle>
          </CardHeader>
          <CardContent>
            {topIngredients.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    values: topIngredients.slice(0, 15).map((item: any) => Number(item.value || item.quantity_used || 0)),
                    labels: topIngredients.slice(0, 15).map((item: any) => String(item.ingredient || '')),
                    type: 'pie',
                  },
                ]}
                layout={{
                  height: 400,
                }}
                animationDelay={0.3}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No usage data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

