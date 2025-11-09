import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/DataTable'
import { Loader2 } from 'lucide-react'

export const Shipments: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['shipments'],
    queryFn: () => apiEndpoints.shipments().then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading shipment data</div>
  }

  const delayAnalysis = data.delay_analysis || []
  const supplierReliability = data.supplier_reliability || []
  const shipments = data.shipments || []

  const avgDelay =
    delayAnalysis.length > 0
      ? delayAnalysis.reduce((sum: number, item: any) => sum + (item.avg_delay || 0), 0) /
        delayAnalysis.length
      : 0

  const maxDelay =
    delayAnalysis.length > 0
      ? Math.max(...delayAnalysis.map((item: any) => item.max_delay || 0))
      : 0

  const totalDelayed =
    delayAnalysis.length > 0
      ? delayAnalysis.reduce((sum: number, item: any) => sum + (item.delayed_count || 0), 0)
      : 0

  const totalShipments =
    delayAnalysis.length > 0
      ? delayAnalysis.reduce((sum: number, item: any) => sum + (item.total_shipments || 0), 0)
      : 1

  const delayRate = totalShipments > 0 ? (totalDelayed / totalShipments) * 100 : 0

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Shipment Analysis</h1>

      {delayAnalysis.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard title="Average Delay (Days)" value={avgDelay.toFixed(2)} />
            <MetricCard title="Max Delay (Days)" value={maxDelay.toFixed(0)} />
            <MetricCard title="Delay Rate" value={`${delayRate.toFixed(1)}%`} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Average Delay by Ingredient</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: delayAnalysis
                      .slice(0, 15)
                      .map((item: any) => item.avg_delay || 0),
                    y: delayAnalysis
                      .slice(0, 15)
                      .map((item: any) => item.ingredient),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: delayAnalysis
                        .slice(0, 15)
                        .map((item: any) => item.avg_delay || 0),
                      colorscale: 'Reds',
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Average Delay (Days)' },
                  yaxis: { title: 'Ingredient' },
                }}
              />
            </CardContent>
          </Card>

          <DataTable
            data={delayAnalysis}
            columns={[
              { key: 'ingredient', label: 'Ingredient', sortable: true },
              {
                key: 'avg_delay',
                label: 'Avg Delay (Days)',
                sortable: true,
                render: value => Number(value).toFixed(2),
              },
              {
                key: 'max_delay',
                label: 'Max Delay (Days)',
                sortable: true,
              },
              {
                key: 'total_shipments',
                label: 'Total Shipments',
                sortable: true,
              },
              {
                key: 'delayed_count',
                label: 'Delayed Count',
                sortable: true,
              },
              {
                key: 'delay_rate',
                label: 'Delay Rate',
                sortable: true,
                render: value => `${Number(value).toFixed(2)}%`,
              },
            ]}
            title="Delay Analysis Details"
            searchable
          />
        </>
      )}

      {supplierReliability.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Supplier Reliability Tracker</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <MetricCard
                  title="Average Reliability Score"
                  value={`${(supplierReliability.reduce((sum: number, item: any) => sum + (item.reliability_score || 0), 0) / supplierReliability.length).toFixed(1)}/100`}
                />
                <MetricCard
                  title="Top Supplier"
                  value={supplierReliability[0]?.supplier || 'N/A'}
                />
                <MetricCard
                  title="Low Reliability Suppliers"
                  value={supplierReliability.filter((item: any) => item.reliability_score < 70).length}
                />
              </div>
              <PlotlyChart
                data={[
                  {
                    x: supplierReliability.map((item: any) => item.reliability_score),
                    y: supplierReliability.map((item: any) => item.supplier),
                    type: 'bar',
                    orientation: 'h',
                    marker: {
                      color: supplierReliability.map((item: any) => item.reliability_score),
                      colorscale: 'RdYlGn',
                    },
                  },
                ]}
                layout={{
                  height: 400,
                  xaxis: { title: 'Reliability Score' },
                  yaxis: { title: 'Supplier' },
                }}
              />
              <DataTable
                data={supplierReliability}
                columns={[
                  { key: 'supplier', label: 'Supplier', sortable: true },
                  {
                    key: 'reliability_score',
                    label: 'Reliability Score',
                    sortable: true,
                  },
                  {
                    key: 'on_time_rate',
                    label: 'On-Time Rate %',
                    sortable: true,
                  },
                  {
                    key: 'fulfillment_rate',
                    label: 'Fulfillment Rate %',
                    sortable: true,
                  },
                  {
                    key: 'avg_delay',
                    label: 'Avg Delay (Days)',
                    sortable: true,
                  },
                ]}
                searchable
              />
            </CardContent>
          </Card>
        </>
      )}

      {shipments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Shipment Details</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={shipments}
              columns={[
                { key: 'ingredient', label: 'Ingredient', sortable: true },
                { key: 'quantity', label: 'Quantity', sortable: true },
                { key: 'unit', label: 'Unit', sortable: true },
                { key: 'num_shipments', label: 'Number of Shipments', sortable: true },
                { key: 'frequency', label: 'Frequency', sortable: true },
              ]}
              searchable
            />
          </CardContent>
        </Card>
      )}

      {delayAnalysis.length === 0 && supplierReliability.length === 0 && shipments.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No shipment data available
          </CardContent>
        </Card>
      )}
    </div>
  )
}

