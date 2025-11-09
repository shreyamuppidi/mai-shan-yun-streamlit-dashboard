import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { cn } from '@/lib/utils'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'

interface Column<T> {
  key: keyof T | string
  label: string
  render?: (value: any, row: T) => React.ReactNode
  sortable?: boolean
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  title?: string
  searchable?: boolean
  searchPlaceholder?: string
  className?: string
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  title,
  searchable = false,
  searchPlaceholder = 'Search...',
  className,
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortKey, setSortKey] = useState<keyof T | string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  const filteredData = useMemo(() => {
    let result = data

    if (searchTerm) {
      result = result.filter((row) =>
        Object.values(row).some((value) =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }

    if (sortKey) {
      result = [...result].sort((a, b) => {
        const aVal = a[sortKey as keyof T]
        const bVal = b[sortKey as keyof T]

        if (aVal === null || aVal === undefined) return 1
        if (bVal === null || bVal === undefined) return -1

        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
        }

        const aStr = String(aVal).toLowerCase()
        const bStr = String(bVal).toLowerCase()

        if (sortDirection === 'asc') {
          return aStr < bStr ? -1 : aStr > bStr ? 1 : 0
        } else {
          return aStr > bStr ? -1 : aStr < bStr ? 1 : 0
        }
      })
    }

    return result
  }, [data, searchTerm, sortKey, sortDirection])

  const handleSort = (key: keyof T | string) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (key: keyof T | string) => {
    if (sortKey !== key) return <ArrowUpDown className="h-4 w-4" />
    return sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
  }

  return (
    <Card className={cn('bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90 border-2 border-white/10 shadow-lg', className)}>
      {title && (
        <CardHeader className="border-b border-white/10">
          <CardTitle className="text-lg font-bold text-white">{title}</CardTitle>
        </CardHeader>
      )}
      <CardContent className="pt-6">
        {searchable && (
          <div className="mb-6">
            <Input
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm bg-white/5 border-white/20 text-white placeholder:text-white/50 focus:border-blue-500/50 focus:ring-blue-500/20"
            />
          </div>
        )}
        <div className="overflow-x-auto rounded-lg border border-white/10">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-white/10 to-white/5 border-b border-white/20">
                {columns.map((column) => (
                  <th
                    key={String(column.key)}
                    className={cn(
                      'text-left p-4 font-semibold text-sm text-white/95 uppercase tracking-wider',
                      column.sortable && 'cursor-pointer hover:bg-white/15 transition-all duration-200 group'
                    )}
                    onClick={() => column.sortable && handleSort(column.key)}
                  >
                    <div className="flex items-center gap-2">
                      {column.label}
                      {column.sortable && (
                        <span className="opacity-60 group-hover:opacity-100 transition-opacity">
                          {getSortIcon(column.key)}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="text-center p-12 text-white/50">
                    <div className="flex flex-col items-center gap-2">
                      <span className="text-2xl">📊</span>
                      <span>No data available</span>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredData.map((row, idx) => (
                  <tr 
                    key={idx} 
                    className={cn(
                      'border-b border-white/5 transition-all duration-200',
                      'hover:bg-gradient-to-r hover:from-white/10 hover:to-transparent',
                      'hover:shadow-lg hover:shadow-blue-500/10',
                      idx % 2 === 0 ? 'bg-white/2' : 'bg-white/1'
                    )}
                  >
                    {columns.map((column) => (
                      <td key={String(column.key)} className="p-4 text-sm text-white/85">
                        {column.render
                          ? column.render(row[column.key as keyof T], row)
                          : String(row[column.key as keyof T] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

