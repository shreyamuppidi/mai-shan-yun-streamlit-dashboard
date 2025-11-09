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
    return (
      <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-red-500/30 shadow-lg">
        <CardContent className="py-16 text-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 flex items-center justify-center">
              <span className="text-4xl">⚠️</span>
            </div>
            <p className="text-red-400 text-lg font-medium">
              Error loading usage trends
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const trends = data.trends || []
  const topIngredients = data.top_ingredients || []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-1 h-10 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full" />
        <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent">
          Usage Trends
        </h1>
      </div>

      {/* Filters */}
      <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-white/10 shadow-lg">
        <CardHeader className="border-b border-white/10">
          <CardTitle className="text-lg font-bold text-white">Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-6 pt-6">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-white/90">Ingredient</label>
            <Select
              value={selectedIngredient}
              onChange={(e) => setSelectedIngredient(e.target.value)}
              className="w-64 bg-white/5 border-white/20 text-white focus:border-blue-500/50 focus:ring-blue-500/20"
            >
              <option value="All">All</option>
              {ingredients.map((ingredient: string) => (
                <option key={ingredient} value={ingredient}>
                  {ingredient}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-white/90">Period</label>
            <Select
              value={period}
              onChange={(e) => setPeriod(e.target.value as 'daily' | 'weekly' | 'monthly')}
              className="w-48 bg-white/5 border-white/20 text-white focus:border-blue-500/50 focus:ring-blue-500/20"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Usage Trend Chart */}
      <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-blue-500/30 shadow-xl">
        <CardHeader className="border-b border-white/10">
          <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
            <span className="w-1 h-6 bg-gradient-to-b from-blue-400 to-cyan-500 rounded-full" />
            Usage Trends ({period.charAt(0).toUpperCase() + period.slice(1)})
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          {trends.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: trends.map((item: any) => String(item.period || item.date || '')),
                  y: trends.map((item: any) => Number(item.quantity_used || item.value || 0)),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Usage',
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
              ]}
              layout={{
                height: 450,
                xaxis: { 
                  title: 'Period',
                  titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                },
                yaxis: { 
                  title: 'Quantity Used',
                  titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                },
                paper_bgcolor: 'rgba(0, 0, 0, 0)',
                plot_bgcolor: 'rgba(0, 0, 0, 0)',
              }}
              animationDelay={0.1}
            />
          ) : (
            <div className="text-center py-12">
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                  <span className="text-3xl">📈</span>
                </div>
                <p className="text-white/60 font-medium">
                  No trend data available for the selected criteria
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Ingredients */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-green-500/30 shadow-xl">
          <CardHeader className="border-b border-white/10">
            <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-1 h-5 bg-gradient-to-b from-green-400 to-emerald-500 rounded-full" />
              Top Ingredients by Usage (Last 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
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
                      colorscale: [
                        [0, 'rgba(34, 197, 94, 0.6)'],
                        [0.5, 'rgba(59, 130, 246, 0.7)'],
                        [1, 'rgba(139, 92, 246, 0.8)'],
                      ],
                      line: {
                        color: 'rgba(255, 255, 255, 0.3)',
                        width: 1,
                      },
                      cmin: Math.min(...topIngredients.map((item: any) => Number(item.value || item.quantity_used || 0))),
                      cmax: Math.max(...topIngredients.map((item: any) => Number(item.value || item.quantity_used || 0))),
                    },
                  },
                ]}
                layout={{
                  height: 450,
                  xaxis: { 
                    title: 'Usage',
                    titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                  },
                  yaxis: { 
                    title: 'Ingredient',
                    categoryorder: 'total ascending',
                    titlefont: { size: 14, color: 'rgba(255, 255, 255, 0.9)' },
                  },
                  paper_bgcolor: 'rgba(0, 0, 0, 0)',
                  plot_bgcolor: 'rgba(0, 0, 0, 0)',
                }}
                animationDelay={0.2}
              />
            ) : (
              <div className="text-center py-12">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-500/20 to-blue-500/20 flex items-center justify-center">
                    <span className="text-3xl">📊</span>
                  </div>
                  <p className="text-white/60 font-medium">
                    No usage data available
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-orange-500/30 shadow-xl">
          <CardHeader className="border-b border-white/10">
            <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-1 h-5 bg-gradient-to-b from-orange-400 to-pink-500 rounded-full" />
              Usage Distribution by Ingredient
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {topIngredients.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    values: topIngredients.slice(0, 15).map((item: any) => Number(item.value || item.quantity_used || 0)),
                    labels: topIngredients.slice(0, 15).map((item: any) => String(item.ingredient || '')),
                    type: 'pie',
                    marker: {
                      colors: [
                        'rgb(59, 130, 246)',   // Blue
                        'rgb(251, 146, 60)',   // Orange
                        'rgb(34, 197, 94)',    // Green
                        'rgb(239, 68, 68)',    // Red
                        'rgb(139, 92, 246)',   // Purple
                        'rgb(236, 72, 153)',   // Pink
                        'rgb(14, 165, 233)',   // Sky Blue
                        'rgb(168, 85, 247)',   // Violet
                        'rgb(20, 184, 166)',   // Teal
                        'rgb(245, 158, 11)',   // Amber
                        'rgb(249, 115, 22)',   // Orange
                        'rgb(6, 182, 212)',    // Cyan
                        'rgb(99, 102, 241)',   // Indigo
                        'rgb(217, 70, 239)',   // Fuchsia
                        'rgb(16, 185, 129)',   // Emerald
                      ],
                      line: {
                        color: 'rgba(0, 0, 0, 0.3)',
                        width: 2,
                      },
                    },
                    textinfo: 'label+percent',
                    textposition: 'outside',
                    hovertemplate: '<b>%{label}</b><br>Usage: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
                  },
                ]}
                layout={{
                  height: 450,
                  paper_bgcolor: 'rgba(0, 0, 0, 0)',
                  plot_bgcolor: 'rgba(0, 0, 0, 0)',
                  font: {
                    color: 'rgba(255, 255, 255, 0.9)',
                    size: 12,
                  },
                  legend: {
                    bgcolor: 'rgba(0, 0, 0, 0.3)',
                    bordercolor: 'rgba(255, 255, 255, 0.2)',
                    borderwidth: 1,
                    font: { color: 'rgba(255, 255, 255, 0.9)', size: 11 },
                  },
                }}
                animationDelay={0.3}
              />
            ) : (
              <div className="text-center py-12">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-500/20 to-pink-500/20 flex items-center justify-center">
                    <span className="text-3xl">🥧</span>
                  </div>
                  <p className="text-white/60 font-medium">
                    No usage data available
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

