import { useState } from 'react'
import { X, Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { useStore } from '../store/useStore'
import { documentApi } from '../services/api'

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')

  const { addDocument, addToast } = useStore()

  if (!isOpen) return null

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) validateAndSetFile(file)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) validateAndSetFile(file)
  }

  const validateAndSetFile = (file: File) => {
    const validTypes = [
      'application/pdf',
      'text/plain',
      'text/markdown',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    const validExtensions = ['.pdf', '.txt', '.md', '.docx']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
      setErrorMessage('Only PDF, TXT, MD, and DOCX files are supported')
      setUploadStatus('error')
      return
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage('File size must be less than 50MB')
      setUploadStatus('error')
      return
    }

    setSelectedFile(file)
    setUploadStatus('idle')
    setErrorMessage('')
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadStatus('uploading')
    setUploadProgress(0)

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      const data = await documentApi.upload(selectedFile)

      clearInterval(progressInterval)
      setUploadProgress(100)
      setUploadStatus('success')

      addDocument({
        doc_id: data.doc_id,
        filename: data.filename,
        file_type: selectedFile.name.split('.').pop() || 'unknown',
        upload_time: new Date().toISOString(),
        status: 'processing',
        total_chunks: 0,
      })

      addToast('Document uploaded successfully!', 'success')

      setTimeout(() => {
        onClose()
        resetModal()
      }, 1500)
    } catch (error) {
      setUploadStatus('error')
      setErrorMessage('Failed to upload document')
      addToast('Upload failed. Please try again.', 'error')
      setErrorMessage('Upload failed. Please try again.')
      console.error('Upload error:', error)
    }
  }

  const resetModal = () => {
    setSelectedFile(null)
    setUploadStatus('idle')
    setUploadProgress(0)
    setErrorMessage('')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Upload Source</h2>
            <p className="text-sm text-gray-600 mt-1">Add documents to your knowledge base</p>
          </div>
          <button
            onClick={() => {
              onClose()
              resetModal()
            }}
            className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
            aria-label="Close modal"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Drag & Drop Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
              isDragging
                ? 'border-blue-500 bg-blue-50 scale-105'
                : 'border-gray-300 hover:border-blue-400 bg-gray-50'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.txt,.md,.docx"
              onChange={handleFileSelect}
              disabled={uploadStatus === 'uploading'}
            />

            {uploadStatus === 'idle' && !selectedFile && (
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <Upload className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
                <p className="text-base font-bold text-gray-900 mb-2">
                  Drop your file here or click to browse
                </p>
                <p className="text-sm text-gray-600">
                  Supports PDF, TXT, MD, DOCX files up to 50MB
                </p>
              </label>
            )}

            {selectedFile && uploadStatus === 'idle' && (
              <div className="space-y-4">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-green-700 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                  <FileText className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
                <div>
                  <p className="text-base font-bold text-gray-900 truncate px-8">{selectedFile.name}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            )}

            {uploadStatus === 'uploading' && (
              <div className="space-y-4">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                  <Loader2 className="w-10 h-10 text-white animate-spin" strokeWidth={2} />
                </div>
                <p className="text-base font-bold text-gray-900">Uploading...</p>
                <div className="max-w-xs mx-auto">
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-700 transition-all duration-300 ease-out rounded-full"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-2 font-semibold">{uploadProgress}%</p>
                </div>
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="space-y-4">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-green-700 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                  <CheckCircle className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
                <p className="text-base font-bold text-green-700">Upload successful!</p>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="space-y-4">
                <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-red-700 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                  <AlertCircle className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
                <p className="text-base font-bold text-red-700">{errorMessage}</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 mt-6">
            <button
              onClick={() => {
                onClose()
                resetModal()
              }}
              className="flex-1 px-5 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all font-semibold"
              disabled={uploadStatus === 'uploading'}
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploadStatus === 'uploading' || uploadStatus === 'success'}
              className="flex-1 px-5 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all font-semibold shadow-lg hover:shadow-xl"
            >
              {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
