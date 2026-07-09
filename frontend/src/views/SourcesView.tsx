import { useEffect, useState } from 'react'
import {
  CheckCircle2,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react'
import { documentApi } from '../services/api'
import { useStore } from '../store/useStore'

interface SourcesViewProps {
  onOpenUpload: () => void
}

export default function SourcesView({ onOpenUpload }: SourcesViewProps) {
  const {
    documents,
    selectedDocIds,
    setDocuments,
    removeDocument,
    toggleDocumentSelection,
    addToast,
  } = useStore()
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setIsLoading(true)
    try {
      const data = await documentApi.list()
      setDocuments(data.documents)
    } catch (error) {
      console.error('Failed to load sources:', error)
      addToast('Failed to load sources', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (docId: string) => {
    try {
      await documentApi.delete(docId)
      removeDocument(docId)
      addToast('Source deleted', 'success')
    } catch (error) {
      console.error('Failed to delete source:', error)
      addToast('Failed to delete source', 'error')
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-100">Source library</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Select files for grounded answers and monitor processing state.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadDocuments}
              className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={onOpenUpload}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Add source
            </button>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="grid grid-cols-[1fr_auto_auto] gap-3 border-b border-gray-200 px-4 py-3 text-xs font-semibold uppercase text-gray-500 dark:border-gray-800 dark:text-gray-400">
            <span>Source</span>
            <span>Status</span>
            <span>Actions</span>
          </div>

          {isLoading && documents.length === 0 ? (
            <div className="flex items-center justify-center gap-2 py-16 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading sources
            </div>
          ) : documents.length === 0 ? (
            <div className="flex min-h-72 items-center justify-center p-6 text-center">
              <div>
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                  <FileText className="h-6 w-6" />
                </div>
                <p className="mt-3 text-sm font-medium text-gray-800 dark:text-gray-200">No sources yet</p>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Add a document to start building your workspace.</p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {documents.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.doc_id)

                return (
                  <div
                    key={doc.doc_id}
                    className={`grid grid-cols-[1fr_auto_auto] items-center gap-3 px-4 py-3 ${
                      isSelected ? 'bg-blue-50 dark:bg-blue-950/40' : ''
                    }`}
                  >
                    <button
                      onClick={() => toggleDocumentSelection(doc.doc_id)}
                      className="min-w-0 text-left"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300'
                        }`}>
                          {isSelected ? <CheckCircle2 className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-gray-950 dark:text-gray-100">{doc.filename}</p>
                          <p className="truncate text-xs text-gray-500 dark:text-gray-400">
                            {doc.file_type.toUpperCase()} · {doc.total_chunks} chunks
                          </p>
                        </div>
                      </div>
                    </button>

                    <SourceStatus status={doc.status} />

                    <button
                      onClick={() => handleDelete(doc.doc_id)}
                      className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 hover:bg-red-50 hover:text-red-600 dark:text-gray-400 dark:hover:bg-red-950 dark:hover:text-red-300"
                      title="Delete source"
                      aria-label="Delete source"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {documents.length > 0 && (
          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
            {selectedDocIds.length} of {documents.length} sources selected for workbench context.
          </p>
        )}
      </div>
    </div>
  )
}

function SourceStatus({ status }: { status: string }) {
  const className =
    status === 'completed'
      ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300'
      : status === 'processing'
        ? 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
        : status === 'failed'
          ? 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
          : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'

  return (
    <span className={`rounded-md px-2 py-1 text-xs font-medium ${className}`}>
      {status}
    </span>
  )
}
