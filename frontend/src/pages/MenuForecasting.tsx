import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { DataTable } from '@/components/DataTable'
import { Loader2 } from 'lucide-react'

export const MenuForecasting: React.FC = () => {
  const [selectedIngredient, setSelectedIngredient] = useState('')
  const [forecastDays, setForecastDays] = useState(30)

  // Fetch available ingredients
  const { data: ingredientsData } = useQuery({
    queryKey: ['ingredients'],
    queryFn: () => apiEndpoints.ingredients().then((res) => res.data),
  })

  const ingredients = ingredientsData?.ingredients || []

  const { data, isLoading, error } = useQuery({
    queryKey: ['menu-forecast', selectedIngredient, forecastDays],
    queryFn: () =>
      selectedIngredient
        ? apiEndpoints.menuForecast(selectedIngredient, forecastDays).then((res) => res.data)
        : null,
    enabled: !!selectedIngredient,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Menu-Driven Ingredient Forecasting</h1>

      <Card>
        <CardHeader>
          <CardTitle>Forecast Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Ingredient</label>
            <Select
              value={selectedIngredient}
              onChange={(e) => setSelectedIngredient(e.target.value)}
              className="w-full"
            >
              <option value="">Select an ingredient...</option>
              {ingredients.map((ingredient: string) => (
                <option key={ingredient} value={ingredient}>
                  {ingredient}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">
              Forecast Days Ahead: {forecastDays}
            </label>
            <Slider
              min={7}
              max={90}
              step={1}
              value={forecastDays}
              onChange={(e) => setForecastDays(Number(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      {error && <div className="text-center text-destructive">Error loading forecast</div>}

      {data && (
        <>
          {(() => {
            const unit = data.unit || 'units'
            const isCountBased = data.is_count_based || false
            const displayUnit = isCountBased ? 'count' : unit
            
            return (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  title="Daily Forecast"
                  value={`${data.summary.daily_forecast.toFixed(isCountBased ? 0 : 1)} ${displayUnit}`}
                />
                <MetricCard
                  title={`Total Forecast (${forecastDays} days)`}
                  value={`${data.summary.total_forecast.toFixed(isCountBased ? 0 : 1)} ${displayUnit}`}
                />
                <MetricCard
                  title="Average Daily"
                  value={`${data.summary.avg_forecast.toFixed(isCountBased ? 0 : 1)} ${displayUnit}`}
                />
              </div>
            )
          })()}

          <Card>
            <CardHeader>
              <CardTitle>Menu-Driven Forecast for {selectedIngredient}</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: data.forecast.map((item: any) => item.date),
                    y: data.forecast.map((item: any) => item.forecasted_usage),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Forecast',
                  },
                  {
                    x: [
                      ...data.forecast.map((item: any) => item.date),
                      ...data.forecast.map((item: any) => item.date).reverse(),
                    ],
                    y: [
                      ...data.forecast.map((item: any) => item.confidence_high),
                      ...data.forecast.map((item: any) => item.confidence_low).reverse(),
                    ],
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Confidence Interval',
                    fill: 'toself',
                    fillcolor: 'rgba(0,100,255,0.2)',
                    line: { color: 'rgba(255,255,255,0)' },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Date' },
                  yaxis: { 
                    title: `Daily Forecasted Usage (${data.unit || 'units'})`,
                  },
                }}
              />
            </CardContent>
          </Card>

          {data.impact_scores && data.impact_scores.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Ingredient Impact Scores by Menu Item</CardTitle>
              </CardHeader>
              <CardContent>
                <PlotlyChart
                  data={[
                    {
                      x: data.impact_scores.map((item: any) => item.impact_score),
                      y: data.impact_scores.map((item: any) => item.menu_item),
                      type: 'bar',
                      orientation: 'h',
                      marker: {
                        color: data.impact_scores.map((item: any) => item.impact_score),
                        colorscale: 'Blues',
                      },
                    },
                  ]}
                  layout={{
                    height: 400,
                    xaxis: { title: 'Impact Score' },
                    yaxis: { title: 'Menu Item' },
                  }}
                />
                <DataTable
                  data={data.impact_scores}
                  columns={[
                    { key: 'menu_item', label: 'Menu Item', sortable: true },
                    {
                      key: 'usage_per_serving',
                      label: `Usage Per Serving (${data.unit || 'units'})`,
                      sortable: true,
                      render: (value: any) => {
                        const isCountBased = data.is_count_based || false
                        return isCountBased ? Math.round(Number(value)) : Number(value).toFixed(2)
                      },
                    },
                    {
                      key: 'popularity_score',
                      label: 'Popularity Score',
                      sortable: true,
                    },
                    {
                      key: 'impact_score',
                      label: 'Impact Score',
                      sortable: true,
                    },
                  ]}
                />
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!selectedIngredient && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Please select an ingredient to view forecast
          </CardContent>
        </Card>
      )}
    </div>
  )
}

