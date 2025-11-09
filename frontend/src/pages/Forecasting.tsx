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

export const Forecasting: React.FC = () => {
  const [selectedIngredient, setSelectedIngredient] = useState('')
  const [forecastDays, setForecastDays] = useState(30)
  const [method, setMethod] = useState<'moving_average' | 'linear_trend'>('moving_average')
  const [includeSeasonality, setIncludeSeasonality] = useState(true)
  const [includeHolidays, setIncludeHolidays] = useState(true)

  // Fetch available ingredients
  const { data: ingredientsData } = useQuery({
    queryKey: ['ingredients'],
    queryFn: () => apiEndpoints.ingredients().then((res) => res.data),
  })

  const ingredients = ingredientsData?.ingredients || []

  const { data, isLoading, error } = useQuery({
    queryKey: ['forecast', selectedIngredient, forecastDays, method, includeSeasonality, includeHolidays],
    queryFn: () =>
      selectedIngredient
        ? apiEndpoints
            .forecast(selectedIngredient, forecastDays, method, includeSeasonality, includeHolidays)
            .then((res) => res.data)
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
      <h1 className="text-3xl font-bold">Demand Forecasting</h1>

      {/* Controls */}
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
          <div>
            <label className="text-sm font-medium mb-2 block">Forecast Method</label>
            <Select value={method} onChange={(e) => setMethod(e.target.value as any)}>
              <option value="moving_average">Moving Average</option>
              <option value="linear_trend">Linear Trend</option>
            </Select>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeSeasonality}
                onChange={(e) => setIncludeSeasonality(e.target.checked)}
              />
              <span className="text-sm">Include Seasonality Adjustments</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeHolidays}
                onChange={(e) => setIncludeHolidays(e.target.checked)}
              />
              <span className="text-sm">Include Holiday Adjustments</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="text-center text-destructive">
          Error loading forecast data
        </div>
      )}

      {data && (
        <>
          {/* Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              title="Average Daily Forecast"
              value={data.summary.avg_forecast.toFixed(2)}
            />
            <MetricCard
              title={`Total Forecast (${forecastDays} days)`}
              value={data.summary.total_forecast.toFixed(2)}
            />
            <MetricCard
              title="Peak Forecast"
              value={data.summary.max_forecast.toFixed(2)}
            />
          </div>

          {/* Seasonality Info */}
          {data.seasonality && (
            <Card>
              <CardHeader>
                <CardTitle>Seasonality Information</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">
                  Peak in month {data.seasonality.peak_month} (factor:{' '}
                  {data.seasonality.peak_factor.toFixed(2)}), Low in month{' '}
                  {data.seasonality.low_month} (factor:{' '}
                  {data.seasonality.low_factor.toFixed(2)})
                </p>
              </CardContent>
            </Card>
          )}

          {/* Forecast Chart */}
          <Card>
            <CardHeader>
              <CardTitle>
                Demand Forecast for {selectedIngredient} - {forecastDays} Day Forecast
              </CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  ...(data.historical && data.historical.length > 0
                    ? [
                        {
                          x: data.historical.map((item: any) => item.period),
                          y: data.historical.map((item: any) => item.quantity_used),
                          type: 'scatter',
                          mode: 'lines+markers',
                          name: 'Historical Usage',
                          line: { color: 'blue', width: 2 },
                        },
                      ]
                    : []),
                  {
                    x: data.forecast.map((item: any) => item.date),
                    y: data.forecast.map((item: any) => item.forecasted_usage),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Forecast',
                    line: { color: 'red', width: 2, dash: 'dash' },
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
                    fillcolor: 'rgba(255,0,0,0.2)',
                    line: { color: 'rgba(255,255,255,0)' },
                    showlegend: true,
                  },
                ]}
                layout={{
                  height: 500,
                  xaxis: { title: 'Date' },
                  yaxis: { title: 'Quantity' },
                }}
                animationDelay={0.1}
              />
            </CardContent>
          </Card>

          {/* Forecast Table */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Forecast</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={data.forecast}
                columns={[
                  { key: 'date', label: 'Date', sortable: true },
                  {
                    key: 'forecasted_usage',
                    label: 'Forecasted Usage',
                    sortable: true,
                    render: (value) => Number(value).toFixed(2),
                  },
                  {
                    key: 'confidence_low',
                    label: 'Confidence Low',
                    sortable: true,
                    render: (value) => Number(value).toFixed(2),
                  },
                  {
                    key: 'confidence_high',
                    label: 'Confidence High',
                    sortable: true,
                    render: (value) => Number(value).toFixed(2),
                  },
                ]}
                searchable
              />
            </CardContent>
          </Card>
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

