import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { DataTable } from '@/components/DataTable'
import { PlotlyChart } from '@/components/PlotlyChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'

export const Inventory: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string[]>(['Low', 'Normal', 'High'])
  const [sortBy, setSortBy] = useState('current_stock')
  const [ascending, setAscending] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => apiEndpoints.inventory().then((res) => res.data.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading inventory data</div>
  }

  const filteredData = data
    .filter((item: any) => statusFilter.includes(item.stock_status))
    .sort((a: any, b: any) => {
      const aVal = a[sortBy]
      const bVal = b[sortBy]
      if (ascending) return aVal > bVal ? 1 : -1
      return aVal < bVal ? 1 : -1
    })

  const topInventory = filteredData.slice(0, 15)

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Inventory Levels</h1>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm">Status:</label>
            <div className="flex gap-2">
              {['Low', 'Normal', 'High'].map((status) => (
                <button
                  key={status}
                  onClick={() => {
                    if (statusFilter.includes(status)) {
                      setStatusFilter(statusFilter.filter((s) => s !== status))
                    } else {
                      setStatusFilter([...statusFilter, status])
                    }
                  }}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    statusFilter.includes(status)
                      ? 'bg-primary text-white'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Sort by:</label>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="current_stock">Current Stock</option>
              <option value="days_until_stockout">Days Until Stockout</option>
              <option value="ingredient">Ingredient</option>
            </Select>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={ascending}
              onChange={(e) => setAscending(e.target.checked)}
            />
            <span className="text-sm">Ascending</span>
          </label>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      <DataTable
        data={filteredData}
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
            key: 'stock_status',
            label: 'Status',
            sortable: true,
            render: (value) => (
              <Badge
                variant={
                  value === 'Low'
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
            key: 'days_until_stockout',
            label: 'Days Until Stockout',
            sortable: true,
            render: (value) => Math.round(Number(value)),
          },
          {
            key: 'reorder_needed',
            label: 'Reorder Needed',
            sortable: true,
            render: (value) => (value ? 'Yes' : 'No'),
          },
        ]}
        title="Current Inventory Levels"
        searchable
      />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Stock Level vs. Thresholds</CardTitle>
          </CardHeader>
          <CardContent>
            <PlotlyChart
              data={[
                {
                  x: topInventory.map((item: any) => item.ingredient),
                  y: topInventory.map((item: any) => item.current_stock),
                  type: 'bar',
                  name: 'Current Stock',
                  marker: { color: 'lightblue' },
                },
                {
                  x: topInventory.map((item: any) => item.ingredient),
                  y: topInventory.map((item: any) => item.min_stock_level),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Min Level',
                  line: { color: 'red', dash: 'dash', width: 2 },
                },
                {
                  x: topInventory.map((item: any) => item.ingredient),
                  y: topInventory.map((item: any) => item.max_stock_level),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Max Level',
                  line: { color: 'green', dash: 'dash', width: 2 },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Ingredient', tickangle: -45 },
                yaxis: { title: 'Quantity' },
              }}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Days Until Stockout</CardTitle>
          </CardHeader>
          <CardContent>
            <PlotlyChart
              data={[
                {
                  x: filteredData
                    .filter((item: any) => item.days_until_stockout < 365)
                    .slice(0, 15)
                    .map((item: any) => item.days_until_stockout),
                  y: filteredData
                    .filter((item: any) => item.days_until_stockout < 365)
                    .slice(0, 15)
                    .map((item: any) => item.ingredient),
                  type: 'bar',
                  orientation: 'h',
                  marker: {
                    color: filteredData
                      .filter((item: any) => item.days_until_stockout < 365)
                      .slice(0, 15)
                      .map((item: any) =>
                        item.days_until_stockout < 7
                          ? 'red'
                          : item.days_until_stockout < 30
                          ? 'orange'
                          : 'yellow'
                      ),
                  },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Days Until Stockout' },
                yaxis: { title: 'Ingredient' },
              }}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

