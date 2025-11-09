import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { DataTable } from '@/components/DataTable'
import { Loader2 } from 'lucide-react'

export const CostWaste: React.FC = () => {
  const [periodDays, setPeriodDays] = useState(30)

  const { data, isLoading, error } = useQuery({
    queryKey: ['waste', periodDays],
    queryFn: () => apiEndpoints.waste(periodDays).then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading waste analysis</div>
  }

  const wasteAnalysis = data.waste_analysis || []
  const heatmapData = data.heatmap_data || []

  const totalWaste = wasteAnalysis.reduce((sum: number, item: any) => sum + (item.waste || 0), 0)
  const totalWasteCost = wasteAnalysis.reduce((sum: number, item: any) => sum + (item.waste_cost || 0), 0)
  const avgWastePercentage =
    wasteAnalysis.length > 0
      ? wasteAnalysis.reduce((sum: number, item: any) => sum + (item.waste_percentage || 0), 0) /
        wasteAnalysis.length
      : 0
  const highRiskItems = heatmapData.filter((item: any) => item.risk_level === 'High Risk').length

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Cost vs. Waste Heatmap</h1>

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

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Total Waste" value={totalWaste.toFixed(2)} />
        <MetricCard
          title="Total Waste Cost"
          value={`$${totalWasteCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        />
        <MetricCard
          title="Average Waste %"
          value={`${avgWastePercentage.toFixed(2)}%`}
        />
        <MetricCard title="High Risk Items" value={highRiskItems} />
      </div>

      {heatmapData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Cost vs. Waste Heatmap</CardTitle>
          </CardHeader>
          <CardContent>
            <PlotlyChart
              data={[
                {
                  x: heatmapData.map((item: any) => item.total_cost || 0),
                  y: heatmapData.map((item: any) => item.waste || 0),
                  mode: 'markers',
                  type: 'scatter',
                  text: heatmapData.map((item: any) => item.ingredient),
                  marker: {
                    size: heatmapData.map((item: any) => Math.max(item.waste_cost || 0, 1) * 10),
                    color: heatmapData.map((item: any) =>
                      item.risk_level === 'High Risk'
                        ? 'red'
                        : item.risk_level === 'Medium Risk'
                        ? 'orange'
                        : 'green'
                    ),
                  },
                },
              ]}
              layout={{
                height: 500,
                xaxis: { title: 'Total Cost ($)' },
                yaxis: { title: 'Waste (units)' },
              }}
            />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Top Waste Items</CardTitle>
        </CardHeader>
        <CardContent>
          {wasteAnalysis.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: wasteAnalysis.slice(0, 15).map((item: any) => item.waste_cost || 0),
                  y: wasteAnalysis.slice(0, 15).map((item: any) => item.ingredient),
                  type: 'bar',
                  orientation: 'h',
                  marker: {
                    color: wasteAnalysis.slice(0, 15).map((item: any) => item.waste_percentage || 0),
                    colorscale: 'Reds',
                  },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Waste Cost ($)' },
                yaxis: { title: 'Ingredient' },
              }}
            />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No waste data available
            </div>
          )}
        </CardContent>
      </Card>

      <DataTable
        data={wasteAnalysis}
        columns={[
          { key: 'ingredient', label: 'Ingredient', sortable: true },
          {
            key: 'total_purchased',
            label: 'Total Purchased',
            sortable: true,
          },
          {
            key: 'total_used',
            label: 'Total Used',
            sortable: true,
          },
          {
            key: 'waste',
            label: 'Waste',
            sortable: true,
          },
          {
            key: 'waste_percentage',
            label: 'Waste %',
            sortable: true,
            render: (value) => `${Number(value).toFixed(2)}%`,
          },
          {
            key: 'total_cost',
            label: 'Total Cost',
            sortable: true,
            render: value => `$${Number(value).toFixed(2)}`,
          },
          {
            key: 'waste_cost',
            label: 'Waste Cost',
            sortable: true,
            render: value => `$${Number(value).toFixed(2)}`,
          },
        ]}
        title="Detailed Waste Analysis"
        searchable
      />
    </div>
  )
}

