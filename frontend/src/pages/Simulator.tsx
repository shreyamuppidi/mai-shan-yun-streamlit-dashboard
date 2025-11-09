import React, { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/DataTable'
import { Loader2 } from 'lucide-react'

export const Simulator: React.FC = () => {
  const [salesMultiplier, setSalesMultiplier] = useState(1.0)
  const [supplierDelayDays, setSupplierDelayDays] = useState(0)
  const [selectedMenuItem, setSelectedMenuItem] = useState('None')
  const [menuItemMultiplier, setMenuItemMultiplier] = useState(1.0)
  const [simulationResults, setSimulationResults] = useState<any>(null)

  // Fetch available menu items
  const { data: menuItemsData } = useQuery({
    queryKey: ['menu-items'],
    queryFn: () => apiEndpoints.menuItems().then((res) => res.data),
  })

  const menuItems = menuItemsData?.menu_items || []

  const simulateMutation = useMutation({
    mutationFn: (scenario: any) => apiEndpoints.simulate(scenario),
    onSuccess: (response) => {
      setSimulationResults(response.data)
    },
    onError: (error: any) => {
      console.error('Simulation error:', error)
      alert(`Error running simulation: ${error.response?.data?.detail || error.message || 'Unknown error'}`)
    },
  })

  const handleRunSimulation = () => {
    const scenario = {
      sales_multiplier: salesMultiplier,
      price_multiplier: 1.0,
      supplier_delay_days: supplierDelayDays,
      menu_item_changes: selectedMenuItem !== 'None' ? { [selectedMenuItem]: menuItemMultiplier } : {},
    }
    simulateMutation.mutate(scenario)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">What-If Simulator</h1>

      <Card>
        <CardHeader>
          <CardTitle>What this does</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          This tool lets you simulate "what if" scenarios to see how changes would affect your
          inventory. Adjust the sliders below to change sales or supplier delays, then click "Run
          Simulation" to see the impact.
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Adjust Scenario Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="text-sm font-medium mb-2 block">
              Change All Sales Volume: {salesMultiplier.toFixed(1)}x
            </label>
            <Slider
              min={0.5}
              max={2.0}
              step={0.1}
              value={salesMultiplier}
              onChange={(e) => setSalesMultiplier(Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {salesMultiplier.toFixed(1)}x means sales would be{' '}
              {(salesMultiplier * 100).toFixed(0)}% of current
            </p>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              Add Supplier Delay (Days): {supplierDelayDays}
            </label>
            <Slider
              min={0}
              max={30}
              step={1}
              value={supplierDelayDays}
              onChange={(e) => setSupplierDelayDays(Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {supplierDelayDays > 0
                ? `Future shipments would arrive ${supplierDelayDays} days later`
                : 'No delay applied'}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Select Menu Item to Change</label>
            <Select
              value={selectedMenuItem}
              onChange={(e) => setSelectedMenuItem(e.target.value)}
              className="w-full"
            >
              <option value="None">None</option>
              {menuItems.map((item: string) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
            {selectedMenuItem !== 'None' && (
              <div className="mt-2">
                <label className="text-sm font-medium mb-2 block">
                  Change {selectedMenuItem} Sales: {menuItemMultiplier.toFixed(1)}x
                </label>
                <Slider
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  value={menuItemMultiplier}
                  onChange={(e) => setMenuItemMultiplier(Number(e.target.value))}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedMenuItem} sales would be {(menuItemMultiplier * 100).toFixed(0)}% of
                  current
                </p>
              </div>
            )}
          </div>

          <Button
            onClick={handleRunSimulation}
            disabled={simulateMutation.isPending}
            className="w-full"
            size="lg"
          >
            {simulateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Simulation...
              </>
            ) : (
              '▶️ Run Simulation'
            )}
          </Button>
        </CardContent>
      </Card>

      {simulateMutation.isError && (
        <Card>
          <CardContent className="py-8 text-center text-destructive">
            Error running simulation: {simulateMutation.error?.message || 'Unknown error'}
          </CardContent>
        </Card>
      )}

      {simulationResults && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              title="Average Stock Change"
              value={simulationResults.summary.avg_stock_change?.toFixed(1) || '0'}
              help="Average change in inventory levels across all ingredients"
            />
            <MetricCard
              title="Ingredients Affected"
              value={simulationResults.summary.items_affected || 0}
              help="Number of ingredients that would see a change in stock"
            />
            <MetricCard
              title="At Risk (Low Stock)"
              value={simulationResults.summary.items_low_stock || 0}
              delta={simulationResults.summary.items_low_stock > 0 ? '⚠️' : undefined}
              deltaType={
                simulationResults.summary.items_low_stock > 0 ? 'decrease' : 'neutral'
              }
              help="Ingredients that would run out in less than 7 days"
            />
            <MetricCard
              title="Avg Days Until Stockout Change"
              value={simulationResults.summary.avg_days_change?.toFixed(1) || '0'}
              help="Average change in days until ingredients run out"
            />
          </div>

          {simulationResults.data && simulationResults.data.length > 0 && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>⚠️ Ingredients with Significant Changes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Showing ingredients with &gt;10% stock change or &gt;7 days change in stockout
                    time
                  </p>
                  {(() => {
                    const significantChanges = simulationResults.data.filter(
                      (item: any) =>
                        Math.abs(item.stock_change_percentage || 0) > 10 ||
                        Math.abs(item.days_change || 0) > 7
                    )
                    return significantChanges.length > 0 ? (
                      <DataTable
                        data={significantChanges}
                        columns={[
                      { key: 'ingredient', label: 'Ingredient', sortable: true },
                      {
                        key: 'current_stock_base',
                        label: 'Current Stock (Now)',
                        sortable: true,
                        render: value => Number(value).toFixed(2),
                      },
                      {
                        key: 'current_stock_simulated',
                        label: 'Current Stock (After Changes)',
                        sortable: true,
                        render: value => Number(value).toFixed(2),
                      },
                      {
                        key: 'stock_change',
                        label: 'Stock Change',
                        sortable: true,
                        render: value => Number(value).toFixed(2),
                      },
                      {
                        key: 'stock_change_percentage',
                        label: 'Stock Change %',
                        sortable: true,
                        render: value => `${Number(value).toFixed(2)}%`,
                      },
                      {
                        key: 'days_until_stockout_base',
                        label: 'Days Until Stockout (Now)',
                        sortable: true,
                        render: value => Math.round(Number(value)),
                      },
                      {
                        key: 'days_until_stockout_simulated',
                        label: 'Days Until Stockout (After Changes)',
                        sortable: true,
                        render: value => Math.round(Number(value)),
                      },
                      {
                        key: 'days_change',
                        label: 'Days Change',
                        sortable: true,
                        render: value => Math.round(Number(value)),
                      },
                        ]}
                        searchable
                      />
                    ) : (
                      <div className="text-center text-muted-foreground py-8">
                        <p>No ingredients show significant changes (&gt;10% stock change or &gt;7 days change)</p>
                        <p className="text-xs mt-2">Showing all ingredients instead:</p>
                        <DataTable
                          data={simulationResults.data}
                          columns={[
                            { key: 'ingredient', label: 'Ingredient', sortable: true },
                            {
                              key: 'current_stock_base',
                              label: 'Current Stock (Now)',
                              sortable: true,
                              render: (value: any) => Number(value).toFixed(2),
                            },
                            {
                              key: 'current_stock_simulated',
                              label: 'Current Stock (After Changes)',
                              sortable: true,
                              render: (value: any) => Number(value).toFixed(2),
                            },
                            {
                              key: 'stock_change',
                              label: 'Stock Change',
                              sortable: true,
                              render: (value: any) => Number(value).toFixed(2),
                            },
                            {
                              key: 'stock_change_percentage',
                              label: 'Stock Change %',
                              sortable: true,
                              render: (value: any) => `${Number(value).toFixed(2)}%`,
                            },
                            {
                              key: 'days_until_stockout_base',
                              label: 'Days Until Stockout (Now)',
                              sortable: true,
                              render: (value: any) => Math.round(Number(value)),
                            },
                            {
                              key: 'days_until_stockout_simulated',
                              label: 'Days Until Stockout (After Changes)',
                              sortable: true,
                              render: (value: any) => Math.round(Number(value)),
                            },
                            {
                              key: 'days_change',
                              label: 'Days Change',
                              sortable: true,
                              render: (value: any) => Math.round(Number(value)),
                            },
                          ]}
                          searchable
                        />
                      </div>
                    )
                  })()}
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Stock Level Changes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {simulationResults.data.length > 0 ? (
                      <PlotlyChart
                        data={[
                          {
                            x: simulationResults.data
                              .filter((item: any) => Math.abs(Number(item.stock_change_percentage || 0)) > 0.01 || Math.abs(Number(item.stock_change || 0)) > 0.01)
                              .slice(0, 15)
                              .map((item: any) => Number(item.stock_change_percentage || 0)),
                            y: simulationResults.data
                              .filter((item: any) => Math.abs(Number(item.stock_change_percentage || 0)) > 0.01 || Math.abs(Number(item.stock_change || 0)) > 0.01)
                              .slice(0, 15)
                              .map((item: any) => String(item.ingredient || '')),
                            type: 'bar',
                            orientation: 'h',
                            marker: {
                              color: simulationResults.data
                                .filter((item: any) => Math.abs(Number(item.stock_change_percentage || 0)) > 0.01 || Math.abs(Number(item.stock_change || 0)) > 0.01)
                                .slice(0, 15)
                                .map((item: any) => Number(item.stock_change || 0)),
                              colorscale: 'RdYlGn',
                            },
                          },
                        ]}
                        layout={{
                          height: 400,
                          xaxis: { title: 'Stock Change (%)' },
                          yaxis: { title: 'Ingredient', categoryorder: 'total ascending' },
                        }}
                      />
                    ) : (
                      <div className="text-center text-muted-foreground py-8">
                        <p>No data available for chart</p>
                        <p className="text-xs mt-2">Note: Most ingredients show 0% change because they already have 0 stock.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Days Until Stockout Changes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {simulationResults.data.length > 0 ? (
                      (() => {
                        const filteredData = simulationResults.data.filter(
                          (item: any) => Math.abs(Number(item.days_change || 0)) > 0.01
                        ).slice(0, 15)
                        return filteredData.length > 0 ? (
                          <PlotlyChart
                            data={[
                              {
                                x: filteredData.map((item: any) => Number(item.days_change || 0)),
                                y: filteredData.map((item: any) => String(item.ingredient || '')),
                                type: 'bar',
                                orientation: 'h',
                                marker: {
                                  color: filteredData.map((item: any) => Number(item.days_change || 0)),
                                  colorscale: 'Reds',
                                },
                              },
                            ]}
                            layout={{
                              height: 400,
                              xaxis: { title: 'Days Change' },
                              yaxis: { title: 'Ingredient', categoryorder: 'total ascending' },
                            }}
                          />
                        ) : (
                          <div className="text-center text-muted-foreground py-8">
                            <p>No changes detected in days until stockout</p>
                            <p className="text-xs mt-2">This is expected when most ingredients already have 0 stock.</p>
                          </div>
                        )
                      })()
                    ) : (
                      <div className="text-center text-muted-foreground py-8">
                        No data available for chart
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

