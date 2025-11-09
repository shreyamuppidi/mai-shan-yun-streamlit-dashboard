import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/DataTable'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'

export const RecipeMapper: React.FC = () => {
  const [filterOption, setFilterOption] = useState<'Can Be Made' | 'Cannot Be Made'>('Can Be Made')

  const { data, isLoading, error } = useQuery({
    queryKey: ['recipe-mapper'],
    queryFn: () => apiEndpoints.recipeMapper().then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading recipe mapper data</div>
  }

  const filteredData =
    filterOption === 'Can Be Made'
      ? data.data.filter((item: any) => item.servings_possible > 0)
      : data.data.filter((item: any) => item.servings_possible === 0)

  const sortedData = [...filteredData].sort(
    (a: any, b: any) => b.servings_possible - a.servings_possible
  )

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Recipe-to-Inventory Mapper</h1>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Overall Menu Viability"
          value={`${data.viability_score.toFixed(1)}%`}
        />
        <MetricCard
          title="Can Be Made"
          value={data.can_make_count}
          help="Number of dishes that can be made with current inventory"
        />
        <MetricCard
          title="Cannot Be Made"
          value={data.cannot_make_count}
          help="Number of dishes that cannot be made (missing ingredients)"
        />
      </div>

      {/* Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Dishes</CardTitle>
        </CardHeader>
        <CardContent>
          <Select
            value={filterOption}
            onChange={(e) => setFilterOption(e.target.value as any)}
          >
            <option value="Can Be Made">Can Be Made</option>
            <option value="Cannot Be Made">Cannot Be Made</option>
          </Select>
        </CardContent>
      </Card>

      {/* Menu Items Table */}
      <DataTable
        data={sortedData}
        columns={[
          { key: 'menu_item', label: 'Menu Item', sortable: true },
          {
            key: 'servings_possible',
            label: 'Servings Possible',
            sortable: true,
            render: (value) => Math.max(0, Math.round(Number(value))),
          },
          ...(sortedData[0]?.viability_status
            ? [
                {
                  key: 'viability_status',
                  label: 'Status',
                  sortable: true,
                  render: (value: any) => (
                    <Badge
                      variant={
                        value === 'High Viability'
                          ? 'default'
                          : value === 'Medium Viability'
                          ? 'secondary'
                          : value === 'Low Viability'
                          ? 'outline'
                          : 'destructive'
                      }
                    >
                      {String(value)}
                    </Badge>
                  ),
                },
              ]
            : []),
          ...(sortedData[0]?.missing_ingredients
            ? [{ key: 'missing_ingredients', label: 'Missing Ingredients', sortable: false }]
            : []),
        ]}
        title="Menu Item Details"
        searchable
      />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Servings Possible by Menu Item</CardTitle>
          </CardHeader>
          <CardContent>
            {sortedData.length > 0 ? (
              <PlotlyChart
                data={[
                  {
                    x: sortedData.slice(0, 15).map((item: any) => item.servings_possible),
                    y: sortedData.slice(0, 15).map((item: any) => item.menu_item),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: sortedData.slice(0, 15).map((item: any) =>
                        item.viability_status === 'High Viability'
                          ? 'green'
                          : item.viability_status === 'Medium Viability'
                          ? 'yellow'
                          : item.viability_status === 'Low Viability'
                          ? 'orange'
                          : 'red'
                      ),
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Servings Possible' },
                  yaxis: { title: 'Menu Item' },
                }}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No data available for selected filter
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Viability Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {sortedData.length > 0 && sortedData[0]?.viability_status ? (
              <PlotlyChart
                data={[
                  {
                    values: Object.values(
                      sortedData.reduce((acc: any, item: any) => {
                        acc[item.viability_status] = (acc[item.viability_status] || 0) + 1
                        return acc
                      }, {})
                    ),
                    labels: Object.keys(
                      sortedData.reduce((acc: any, item: any) => {
                        acc[item.viability_status] = (acc[item.viability_status] || 0) + 1
                        return acc
                      }, {})
                    ),
                    type: 'pie',
                    marker: {
                      colors: ['green', 'yellow', 'orange', 'red'],
                    },
                  },
                ]}
                layout={{
                  height: 400,
                }}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No status data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

