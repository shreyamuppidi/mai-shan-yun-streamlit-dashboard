import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiEndpoints } from '@/services/api'
import { DataUpload } from '@/components/DataUpload'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/DataTable'
import { Loader2, FileText, Calendar, HardDrive } from 'lucide-react'
import { format } from 'date-fns'

export const DataManagement: React.FC = () => {
  const { data: uploadHistory, isLoading, refetch } = useQuery({
    queryKey: ['upload-history'],
    queryFn: () => apiEndpoints.uploadHistory().then((res) => res.data),
  })

  const handleUploadComplete = () => {
    // Refetch upload history after successful upload
    refetch()
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const formatDate = (dateString: string): string => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
    } catch {
      return dateString
    }
  }

  const historyColumns = [
    {
      key: 'filename',
      label: 'Filename',
      render: (value: any, row: any) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          <span className="font-mono text-sm">{String(value)}</span>
        </div>
      ),
      sortable: true,
    },
    {
      key: 'size_mb',
      label: 'Size',
      render: (value: any, row: any) => (
        <div className="flex items-center gap-2">
          <HardDrive className="h-4 w-4 text-white/40" />
          <span>{formatFileSize(row.size_bytes)}</span>
        </div>
      ),
      sortable: true,
    },
    {
      key: 'uploaded_at',
      label: 'Uploaded',
      render: (value: any, row: any) => (
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-white/40" />
          <span>{formatDate(String(value))}</span>
        </div>
      ),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Data Management</h1>
        <p className="text-white/60">
          Upload monthly data files and manage your data upload history
        </p>
      </div>

      <DataUpload onUploadComplete={handleUploadComplete} />

      <Card>
        <CardHeader>
          <CardTitle>Upload History</CardTitle>
          <CardDescription>
            View all uploaded data files with their metadata
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : uploadHistory?.files && uploadHistory.files.length > 0 ? (
            <DataTable
              data={uploadHistory.files}
              columns={historyColumns}
            />
          ) : (
            <div className="text-center py-12 text-white/60">
              <FileText className="h-12 w-12 mx-auto mb-4 text-white/30" />
              <p>No upload history available</p>
              <p className="text-sm mt-2">Upload a file to see it here</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

