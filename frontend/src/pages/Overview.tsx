import React from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { MetricCard } from '@/components/MetricCard'
import { PlotlyChart } from '@/components/PlotlyChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/DataTable'
import { Loader2 } from 'lucide-react'

export const Overview: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['overview'],
    queryFn: () => apiEndpoints.overview().then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <div className="text-destructive mb-4">Error loading overview data</div>
        <div className="text-sm text-muted-foreground">
          {error instanceof Error ? error.message : 'Unknown error'}
        </div>
        <div className="text-sm text-muted-foreground mt-2">
          Make sure the backend is running on http://localhost:8000
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  // Status distribution pie chart
  const statusChartData = data.status_distribution && Object.keys(data.status_distribution).length > 0 ? [
    {
      values: Object.values(data.status_distribution).map(v => Number(v)),
      labels: Object.keys(data.status_distribution),
      type: 'pie',
      hole: 0.4,
      marker: {
        colors: ['#ff4444', '#44ff44', '#ffaa44'],
      },
    },
  ] : []

  // Critical stockout bar chart
  const stockoutChartData = data.critical_stockout && data.critical_stockout.length > 0 ? [
    {
      x: data.critical_stockout.map((item: any) => Number(item.days_until_stockout || 0)),
      y: data.critical_stockout.map((item: any, index: number) => {
        // Add small offset to prevent complete overlap when all values are 0
        const baseY = String(item.ingredient || '')
        return baseY
      }),
      type: 'bar',
      orientation: 'h',
      marker: { 
        color: data.critical_stockout.map((item: any) => {
          const days = Number(item.days_until_stockout || 0)
          if (days <= 0) return 'rgb(220, 38, 38)' // Red for out of stock
          if (days < 7) return 'rgb(255, 140, 0)' // Orange for critical
          return 'rgb(255, 200, 0)' // Yellow for warning
        }),
      },
      text: data.critical_stockout.map((item: any) => 
        `${item.ingredient || ''}: ${Number(item.days_until_stockout || 0)} days`
      ),
      textposition: 'outside',
    },
  ] : []

  // Top risks scatter plot - use bar chart when all points overlap
  const riskChartData = data.top_risks && data.top_risks.length > 0 ? (() => {
    const allStocksZero = data.top_risks.every((item: any) => Number(item.current_stock || 0) === 0)
    const allRisksSame = new Set(data.top_risks.map((item: any) => Number(item.risk_score || 0))).size === 1
    
    // If all points overlap, use a bar chart instead
    if (allStocksZero && allRisksSame) {
      return [
        {
          x: data.top_risks.map((item: any) => Number(item.risk_score || 0)),
          y: data.top_risks.map((item: any) => String(item.ingredient || '')),
          type: 'bar',
          orientation: 'h',
          marker: {
            color: data.top_risks.map((item: any) => Number(item.risk_score || 0)),
            colorscale: 'Reds',
            showscale: true,
            colorbar: { title: 'Risk Score' },
          },
          text: data.top_risks.map((item: any) => 
            `${item.ingredient || ''}: ${Number(item.risk_score || 0)}`
          ),
          textposition: 'outside',
        },
      ]
    }
    
    // Otherwise use scatter plot
    return [
      {
        x: data.top_risks.map((item: any) => Number(item.current_stock || 0)),
        y: data.top_risks.map((item: any) => Number(item.risk_score || 0)),
        mode: 'markers+text',
        type: 'scatter',
        text: data.top_risks.map((item: any) => String(item.ingredient || '')),
        textposition: 'top center',
        textfont: { size: 10 },
        marker: {
          size: data.top_risks.map((item: any) => Math.max(8, Math.min(30, (Number(item.usage_velocity_7d || 0) + 1) * 3))),
          color: data.top_risks.map((item: any) => Number(item.risk_score || 0)),
          colorscale: 'Reds',
          showscale: true,
          colorbar: { title: 'Risk Score' },
        },
      },
    ]
  })() : []

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-4xl font-bold text-white mb-6"
      >
        Inventory Intelligence Dashboard
      </motion.h1>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Ingredients"
          value={data.metrics.total_ingredients}
          help="Total number of ingredients tracked"
          animationDelay={0.1}
        />
        <MetricCard
          title="Low Stock Items"
          value={data.metrics.low_stock}
          delta={`-${data.metrics.low_stock} need reorder`}
          deltaType="decrease"
          help="Ingredients below minimum stock level"
          animationDelay={0.2}
        />
        <MetricCard
          title="Overstocked Items"
          value={data.metrics.high_stock}
          help="Ingredients above maximum stock level"
          animationDelay={0.3}
        />
        <MetricCard
          title="Reorder Needed"
          value={data.metrics.reorder_count}
          delta={data.metrics.reorder_count > 0 ? 'Urgent' : undefined}
          deltaType={data.metrics.reorder_count > 0 ? 'decrease' : 'neutral'}
          help="Items that need immediate reordering"
          animationDelay={0.4}
        />
        <MetricCard
          title="Menu Viability"
          value={data.metrics.menu_viability ? `${data.metrics.menu_viability.toFixed(0)}%` : 'N/A'}
          help="Percentage of menu items that can be made with current stock"
          animationDelay={0.5}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Inventory Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {statusChartData && statusChartData.length > 0 && statusChartData[0]?.values && statusChartData[0].values.length > 0 ? (
              <PlotlyChart
                data={statusChartData}
                layout={{
                  height: 400,
                  showlegend: true,
                }}
                animationDelay={0.6}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No status data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Items Needing Reorder</CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_risks && data.top_risks.length > 0 ? (
              (() => {
                const itemsNeedingReorder = data.top_risks
                  .filter((item: any) => item.needs_reorder || item.current_stock === 0)
                  .slice(0, 10)
                
                return itemsNeedingReorder.length > 0 ? (
                  <DataTable
                    data={itemsNeedingReorder}
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
                        key: 'days_until_stockout',
                        label: 'Days Until Stockout',
                        sortable: true,
                        render: (value) => {
                          const days = Number(value || 0)
                          if (days <= 0) return <span className="text-red-600 font-semibold">Out of Stock</span>
                          if (days < 7) return <span className="text-orange-600 font-semibold">{Math.round(days)}</span>
                          return <span>{Math.round(days)}</span>
                        },
                      },
                    ]}
                    searchable
                  />
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    ✅ No items currently need reordering
                  </div>
                )
              })()
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No risk data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top 10 Ingredients by Current Stock</CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_stock && data.top_stock.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    x: data.top_stock.map((item: any) => Number(item.current_stock || 0)),
                    y: data.top_stock.map((item: any) => String(item.ingredient || '')),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: data.top_stock.map((item: any) =>
                        item.stock_status === 'Low'
                          ? '#ff4444'
                          : item.stock_status === 'High'
                          ? '#ffaa44'
                          : '#44ff44'
                      ),
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Current Stock' },
                  yaxis: { title: 'Ingredient', categoryorder: 'total ascending' },
                }}
                animationDelay={0.7}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No stock data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Risk Items</CardTitle>
          </CardHeader>
          <CardContent>
            {riskChartData.length > 0 ? (
              (() => {
                const isBarChart = riskChartData[0]?.type === 'bar'
                return (
                  <PlotlyChart
                    data={riskChartData}
                    layout={{
                      height: 400,
                      xaxis: { 
                        title: isBarChart ? 'Risk Score' : 'Current Stock',
                        type: 'linear',
                        ...(isBarChart ? { range: [0, 100] } : {}),
                      },
                      yaxis: { 
                        title: isBarChart ? 'Ingredient' : 'Risk Score',
                        type: isBarChart ? undefined : 'linear',
                        ...(isBarChart ? { categoryorder: 'total ascending' } : { range: [0, 100] }),
                      },
                      hovermode: 'closest',
                    }}
                    animationDelay={0.8}
                  />
                )
              })()
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No risk data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Purchases</CardTitle>
          </CardHeader>
          <CardContent>
            {data.recent_purchases && data.recent_purchases.length > 0 ? (
              <DataTable
                data={data.recent_purchases}
                columns={[
                  { key: 'date', label: 'Date', sortable: true },
                  { key: 'ingredient', label: 'Ingredient', sortable: true },
                  { key: 'quantity', label: 'Quantity', sortable: true },
                  {
                    key: 'total_cost',
                    label: 'Total Cost ($)',
                    sortable: true,
                    render: (value) => `$${Number(value).toFixed(2)}`,
                  },
                ]}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No purchase data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Usage</CardTitle>
          </CardHeader>
          <CardContent>
            {data.recent_usage && data.recent_usage.length > 0 ? (
              <DataTable
                data={data.recent_usage}
                columns={[
                  { key: 'date', label: 'Date', sortable: true },
                  { key: 'ingredient', label: 'Ingredient', sortable: true },
                  { key: 'quantity_used', label: 'Quantity Used', sortable: true },
                  ...(data.recent_usage[0]?.menu_item
                    ? [{ key: 'menu_item', label: 'Menu Item', sortable: true }]
                    : []),
                ]}
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

