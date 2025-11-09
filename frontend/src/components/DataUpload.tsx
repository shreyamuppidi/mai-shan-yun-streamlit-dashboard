import React, { useState, useRef } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { apiEndpoints } from '@/services/api'
import { useQueryClient } from '@tanstack/react-query'

interface DataUploadProps {
  onUploadComplete?: (result: any) => void
  onError?: (error: string) => void
}

export const DataUpload: React.FC<DataUploadProps> = ({ onUploadComplete, onError }) => {
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const validateFile = (file: File): string | null => {
    // Validate file type
    const validTypes = ['.xlsx', '.csv']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!validTypes.includes(fileExt)) {
      return `Invalid file type. Only ${validTypes.join(', ')} files are allowed.`
    }
    
    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (file.size > maxSize) {
      return `File too large. Maximum size is 50MB.`
    }
    
    return null
  }

  const handleFileSelect = (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      setSelectedFile(null)
      if (onError) onError(validationError)
      return
    }
    
    setSelectedFile(file)
    setError(null)
    setUploadResult(null)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
    
    if (uploading) return
    
    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    
    setUploading(true)
    setError(null)
    setUploadResult(null)
    
    try {
      const response = await apiEndpoints.uploadData(selectedFile)
      const result = response.data
      
      setUploadResult(result)
      
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries()
      
      // Also call reload endpoint to ensure backend cache is refreshed
      await apiEndpoints.reload()
      
      if (onUploadComplete) {
        onUploadComplete(result)
      }
      
      // Clear selected file after successful upload
      setTimeout(() => {
        setSelectedFile(null)
        setUploadResult(null)
      }, 5000)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Upload failed'
      setError(errorMsg)
      if (onError) onError(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    setError(null)
    setUploadResult(null)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Upload Data File</CardTitle>
          <CardDescription>
            Upload monthly Excel (.xlsx) or CSV (.csv) data files. Maximum file size: 50MB
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!selectedFile && !uploadResult && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleClick}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                transition-all duration-200
                ${
                  isDragActive
                    ? 'border-primary bg-primary/10'
                    : 'border-white/30 hover:border-white/50 hover:bg-white/5'
                }
                ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.csv"
                onChange={handleFileInputChange}
                className="hidden"
                disabled={uploading}
              />
              <Upload className="h-12 w-12 mx-auto mb-4 text-white/60" />
              <p className="text-white/80 mb-2">
                {isDragActive ? 'Drop the file here' : 'Drag & drop a file here, or click to select'}
              </p>
              <p className="text-sm text-white/50">
                Supports .xlsx and .csv files
              </p>
            </div>
          )}

          {selectedFile && !uploadResult && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/20">
                <div className="flex items-center gap-3">
                  <File className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-white font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-white/60">{formatFileSize(selectedFile.size)}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleRemoveFile}
                  disabled={uploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <Button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload File
                  </>
                )}
              </Button>
            </div>
          )}

          {uploadResult && (
            <div className="space-y-4">
              <div className="p-4 bg-green-500/20 border border-green-500/50 rounded-lg">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-green-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-green-400 font-medium mb-2">Upload Successful!</p>
                    <div className="text-sm text-white/80 space-y-1">
                      <p>File: {uploadResult.file.original_filename}</p>
                      <p>Size: {uploadResult.file.size_mb} MB</p>
                      {uploadResult.merge_stats && (
                        <div className="mt-2 pt-2 border-t border-green-500/30">
                          <p className="font-medium text-green-300">Merge Statistics:</p>
                          <ul className="list-disc list-inside space-y-1 mt-1">
                            <li>New records: {uploadResult.merge_stats.total_new_records}</li>
                            <li>Duplicates skipped: {uploadResult.merge_stats.total_duplicates}</li>
                            {uploadResult.merge_stats.stats && (
                              <>
                                <li>
                                  Purchases: {uploadResult.merge_stats.stats.purchases.new} new,{' '}
                                  {uploadResult.merge_stats.stats.purchases.duplicates} duplicates
                                </li>
                                <li>
                                  Sales: {uploadResult.merge_stats.stats.sales.new} new,{' '}
                                  {uploadResult.merge_stats.stats.sales.duplicates} duplicates
                                </li>
                                <li>
                                  Usage: {uploadResult.merge_stats.stats.usage.new} new,{' '}
                                  {uploadResult.merge_stats.stats.usage.duplicates} duplicates
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <Button
                onClick={() => {
                  setSelectedFile(null)
                  setUploadResult(null)
                  setError(null)
                }}
                variant="outline"
                className="w-full"
              >
                Upload Another File
              </Button>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-400 font-medium mb-1">Upload Failed</p>
                  <p className="text-sm text-white/80">{error}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

