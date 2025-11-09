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
      <div className="flex items-center gap-3 mb-2">
        <div className="w-1 h-10 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full" />
        <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent">
          Menu-Driven Ingredient Forecasting
        </h1>
      </div>

      <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-white/10 shadow-lg">
        <CardHeader className="border-b border-white/10">
          <CardTitle className="text-lg font-bold text-white">Forecast Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div>
            <label className="text-sm font-semibold mb-3 block text-white/90">
              Ingredient
            </label>
            <Select
              value={selectedIngredient}
              onChange={(e) => setSelectedIngredient(e.target.value)}
              className="w-full bg-white/5 border-white/20 text-white focus:border-blue-500/50 focus:ring-blue-500/20"
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
            <label className="text-sm font-semibold mb-3 block text-white/90">
              Forecast Days Ahead: <span className="text-blue-400 font-bold">{forecastDays}</span>
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <MetricCard
                  title="Daily Forecast"
                  value={`${data.summary.daily_forecast.toFixed(isCountBased ? 0 : 1)} ${displayUnit}`}
                  gradient="blue"
                  animationDelay={0.1}
                />
                <MetricCard
                  title={`Total Forecast (${forecastDays} days)`}
                  value={`${data.summary.total_forecast.toFixed(isCountBased ? 0 : 1)} ${displayUnit}`}
                  gradient="purple"
                  animationDelay={0.2}
                />
                <MetricCard
                  title="Average Daily"
                  value={`${data.summary.avg_forecast.toFixed(isCountBased ? 0 : 1)} ${displayUnit}`}
                  gradient="green"
                  animationDelay={0.3}
                />
              </div>
            )
          })()}

          <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-blue-500/30 shadow-xl">
            <CardHeader className="border-b border-white/10">
              <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-blue-400 to-purple-500 rounded-full" />
                Menu-Driven Forecast for {selectedIngredient}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <PlotlyChart
                data={[
                  {
                    x: data.forecast.map((item: any) => item.date),
                    y: data.forecast.map((item: any) => item.forecasted_usage),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Forecast',
                    line: {
                      color: 'rgb(59, 130, 246)',
                      width: 3,
                      shape: 'spline',
                    },
                    marker: {
                      color: 'rgb(59, 130, 246)',
                      size: 8,
                      line: {
                        color: 'rgb(255, 255, 255)',
                        width: 2,
                      },
                    },
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
                    fillcolor: 'rgba(59, 130, 246, 0.15)',
                    line: { color: 'rgba(255,255,255,0)' },
                    hoverinfo: 'skip',
                  },
                ]}
                layout={{
                  height: 450,
                  xaxis: { 
                    title: 'Date',
                    titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                  },
                  yaxis: { 
                    title: `Daily Forecasted Usage (${data.unit || 'units'})`,
                    titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                  },
                  paper_bgcolor: 'rgba(0, 0, 0, 0)',
                  plot_bgcolor: 'rgba(0, 0, 0, 0)',
                }}
                animationDelay={0.4}
              />
            </CardContent>
          </Card>

          {data.impact_scores && data.impact_scores.length > 0 && (
            <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-purple-500/30 shadow-xl">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
                  <span className="w-1 h-6 bg-gradient-to-b from-purple-400 to-pink-500 rounded-full" />
                  Ingredient Impact Scores by Menu Item
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                <PlotlyChart
                  data={[
                    {
                      x: data.impact_scores.map((item: any) => item.impact_score),
                      y: data.impact_scores.map((item: any) => item.menu_item),
                      type: 'bar',
                      orientation: 'h',
                      marker: {
                        color: data.impact_scores.map((item: any) => item.impact_score),
                        colorscale: [
                          [0, 'rgba(99, 102, 241, 0.6)'],
                          [0.5, 'rgba(139, 92, 246, 0.7)'],
                          [1, 'rgba(236, 72, 153, 0.8)'],
                        ],
                        line: {
                          color: 'rgba(255, 255, 255, 0.3)',
                          width: 1,
                        },
                        cmin: Math.min(...data.impact_scores.map((item: any) => item.impact_score)),
                        cmax: Math.max(...data.impact_scores.map((item: any) => item.impact_score)),
                      },
                    },
                  ]}
                  layout={{
                    height: 400,
                    xaxis: { 
                      title: 'Impact Score',
                      titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                    },
                    yaxis: { 
                      title: 'Menu Item',
                      titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                    },
                    paper_bgcolor: 'rgba(0, 0, 0, 0)',
                    plot_bgcolor: 'rgba(0, 0, 0, 0)',
                  }}
                  animationDelay={0.5}
                />
                <div className="pt-4">
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
                          return (
                            <span className="font-medium text-blue-300">
                              {isCountBased ? Math.round(Number(value)) : Number(value).toFixed(2)}
                            </span>
                          )
                        },
                      },
                      {
                        key: 'popularity_score',
                        label: 'Popularity Score',
                        sortable: true,
                        render: (value: any) => (
                          <span className="font-medium text-purple-300">
                            {Number(value).toFixed(2)}
                          </span>
                        ),
                      },
                      {
                        key: 'impact_score',
                        label: 'Impact Score',
                        sortable: true,
                        render: (value: any) => (
                          <span className="font-bold text-pink-300">
                            {Number(value).toFixed(2)}
                          </span>
                        ),
                      },
                    ]}
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!selectedIngredient && (
        <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-white/10 shadow-lg">
          <CardContent className="py-16 text-center">
            <div className="flex flex-col items-center gap-4">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                <span className="text-4xl">📊</span>
              </div>
              <p className="text-white/70 text-lg font-medium">
                Please select an ingredient to view forecast
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

