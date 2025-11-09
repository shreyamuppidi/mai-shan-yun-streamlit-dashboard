import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { PlotlyChart } from '@/components/PlotlyChart'
import { MetricCard } from '@/components/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { DataTable } from '@/components/DataTable'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'

export const Storage: React.FC = () => {
  const [daysAhead, setDaysAhead] = useState(7)

  const { data, isLoading, error } = useQuery({
    queryKey: ['storage', daysAhead],
    queryFn: () => apiEndpoints.storage(daysAhead).then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="text-center text-destructive">Error loading storage data</div>
  }

  const storageData = data.data || []
  const summary = data.summary || {}

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Cold Storage Load Estimator</h1>

      <Card>
        <CardHeader>
          <CardTitle>Estimate Storage Load</CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <label className="text-sm font-medium mb-2 block">
              Days Ahead: {daysAhead}
            </label>
            <Slider
              min={1}
              max={30}
              step={1}
              value={daysAhead}
              onChange={(e) => setDaysAhead(Number(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Total Current Load"
          value={`${summary.total_current_load?.toFixed(2) || '0.00'} cu ft`}
        />
        <MetricCard
          title="Total Incoming Load"
          value={`${summary.total_incoming_load?.toFixed(2) || '0.00'} cu ft`}
        />
        <MetricCard
          title="Overloaded Storage Types"
          value={summary.overloaded_count || 0}
          delta={summary.overloaded_count > 0 ? '⚠️' : undefined}
          deltaType={summary.overloaded_count > 0 ? 'decrease' : 'neutral'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Storage Load by Type</CardTitle>
        </CardHeader>
        <CardContent>
          {storageData.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: storageData.map((item: any) => item.storage_type),
                  y: storageData.map((item: any) => item.current_load || 0),
                  type: 'bar',
                  name: 'Current Load',
                  marker: { color: 'lightblue' },
                },
                {
                  x: storageData.map((item: any) => item.storage_type),
                  y: storageData.map((item: any) => item.incoming_load || 0),
                  type: 'bar',
                  name: 'Incoming Load',
                  marker: { color: 'orange' },
                },
                {
                  x: storageData.map((item: any) => item.storage_type),
                  y: storageData.map((item: any) => item.estimated_capacity || 0),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Estimated Capacity',
                  line: { color: 'red', width: 2, dash: 'dash' },
                },
              ]}
              layout={{
                height: 400,
                barmode: 'group',
                xaxis: { title: 'Storage Type' },
                yaxis: { title: 'Load (cubic feet)' },
              }}
            />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No storage data available
            </div>
          )}
        </CardContent>
      </Card>

      <DataTable
        data={storageData}
        columns={[
          { key: 'storage_type', label: 'Storage Type', sortable: true },
          {
            key: 'current_load',
            label: 'Current Load',
            sortable: true,
            render: value => `${Number(value).toFixed(2)} cu ft`,
          },
          {
            key: 'incoming_load',
            label: 'Incoming Load',
            sortable: true,
            render: value => `${Number(value).toFixed(2)} cu ft`,
          },
          {
            key: 'total_load',
            label: 'Total Load',
            sortable: true,
            render: value => `${Number(value).toFixed(2)} cu ft`,
          },
          {
            key: 'estimated_capacity',
            label: 'Estimated Capacity',
            sortable: true,
            render: value => `${Number(value).toFixed(2)} cu ft`,
          },
          {
            key: 'utilization_percentage',
            label: 'Utilization %',
            sortable: true,
            render: (value) => `${Number(value).toFixed(2)}%`,
          },
          {
            key: 'is_overloaded',
            label: 'Is Overloaded',
            sortable: true,
            render: value => (
              <Badge variant={value ? 'destructive' : 'default'}>
                {value ? 'Yes' : 'No'}
              </Badge>
            ),
          },
        ]}
        title="Storage Load Details"
        searchable
      />

      <Card>
        <CardHeader>
          <CardTitle>Storage Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          {storageData.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: storageData.map((item: any) => item.storage_type),
                  y: storageData.map((item: any) => item.utilization_percentage || 0),
                  type: 'bar',
                  marker: {
                    color: storageData.map((item: any) =>
                      item.is_overloaded ? 'red' : 'green'
                    ),
                  },
                },
              ]}
              layout={{
                height: 400,
                xaxis: { title: 'Storage Type' },
                yaxis: { title: 'Utilization %' },
                shapes: [
                  {
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    y0: 100,
                    y1: 100,
                    xref: 'paper',
                    yref: 'y',
                    line: { color: 'red', width: 2, dash: 'dash' },
                  },
                ],
                annotations: [
                  {
                    x: 0.5,
                    y: 100,
                    xref: 'paper',
                    yref: 'y',
                    text: '100% Capacity',
                    showarrow: false,
                    font: { color: 'red' },
                  },
                ],
              }}
            />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No utilization data available
            </div>
          )}
        </CardContent>
      </Card>

      {storageData.filter((item: any) => item.is_overloaded).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>⚠️ Overload Warnings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {storageData
              .filter((item: any) => item.is_overloaded)
              .map((item: any) => (
                <div key={item.storage_type} className="p-4 border rounded-lg bg-destructive/10">
                  <p className="font-semibold">{item.storage_type} storage is overloaded!</p>
                  <p className="text-sm text-muted-foreground">
                    Current + Incoming: {item.total_load?.toFixed(2)} cu ft, Capacity:{' '}
                    {item.estimated_capacity?.toFixed(2)} cu ft
                  </p>
                </div>
              ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

