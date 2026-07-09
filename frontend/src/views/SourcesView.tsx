import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CheckCircle2,
  FileText,
  Folder,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Tag,
  Trash2,
} from 'lucide-react'
import { documentApi, spacesApi, type SpaceItem } from '../services/api'
import { useStore } from '../store/useStore'

interface SourcesViewProps {
  onOpenUpload: () => void
}

const statusOptions: Array<{ label: string; value: string | null }> = [
  { label: 'All', value: null },
  { label: 'Ready', value: 'completed' },
  { label: 'Processing', value: 'processing' },
  { label: 'Failed', value: 'failed' },
]

export default function SourcesView({ onOpenUpload }: SourcesViewProps) {
  const {
    documents,
    selectedDocIds,
    activeSpaceId,
    sourceQuery,
    sourceStatusFilter,
    sourceTagFilter,
    setDocuments,
    removeDocument,
    toggleDocumentSelection,
    setActiveSpaceId,
    setSourceQuery,
    setSourceStatusFilter,
    setSourceTagFilter,
    addToast,
  } = useStore()
  const [spaces, setSpaces] = useState<SpaceItem[]>([])
  const [newSpaceName, setNewSpaceName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingSpaces, setIsLoadingSpaces] = useState(false)
  const [isAssigning, setIsAssigning] = useState(false)

  const activeSpace = useMemo(
    () => spaces.find((space) => space.space_id === activeSpaceId) ?? null,
    [activeSpaceId, spaces],
  )
  const tagFilterValue = sourceTagFilter.join(', ')

  const loadSpaces = useCallback(async () => {
    setIsLoadingSpaces(true)
    try {
      const data = await spacesApi.list()
      setSpaces(data.spaces)
      if (activeSpaceId && !data.spaces.some((space) => space.space_id === activeSpaceId)) {
        setActiveSpaceId(null)
      }
    } catch (error) {
      console.error('Failed to load spaces:', error)
      addToast('Failed to load spaces', 'error')
    } finally {
      setIsLoadingSpaces(false)
    }
  }, [activeSpaceId, addToast, setActiveSpaceId])

  const loadDocuments = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await documentApi.search({
        query: sourceQuery.trim(),
        space_id: activeSpaceId,
        tags: sourceTagFilter,
        status: sourceStatusFilter,
      })
      setDocuments(data.documents)
    } catch (error) {
      console.error('Failed to load sources:', error)
      addToast('Failed to load sources', 'error')
    } finally {
      setIsLoading(false)
    }
  }, [
    activeSpaceId,
    addToast,
    setDocuments,
    sourceQuery,
    sourceStatusFilter,
    sourceTagFilter,
  ])

  useEffect(() => {
    void loadSpaces()
  }, [loadSpaces])

  useEffect(() => {
    void loadDocuments()
  }, [loadDocuments])

  const handleRefresh = async () => {
    await Promise.all([loadSpaces(), loadDocuments()])
  }

  const handleCreateSpace = async () => {
    const name = newSpaceName.trim()
    if (!name) return

    try {
      const space = await spacesApi.create({ name })
      setSpaces((current) => [space, ...current])
      setActiveSpaceId(space.space_id)
      setNewSpaceName('')
      addToast('Space created', 'success')
    } catch (error) {
      console.error('Failed to create space:', error)
      addToast('Failed to create space', 'error')
    }
  }

  const handleAssignSelected = async () => {
    if (!activeSpaceId || selectedDocIds.length === 0) return

    setIsAssigning(true)
    try {
      await Promise.all(
        selectedDocIds.map((docId) => spacesApi.assignDocument(activeSpaceId, docId)),
      )
      await loadDocuments()
      addToast('Sources assigned to space', 'success')
    } catch (error) {
      console.error('Failed to assign sources:', error)
      addToast('Failed to assign sources', 'error')
    } finally {
      setIsAssigning(false)
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

  const handleTagFilterChange = (value: string) => {
    setSourceTagFilter(
      value
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-100">Source library</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {activeSpace ? activeSpace.name : 'All sources'} · {documents.length} visible
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading || isLoadingSpaces ? 'animate-spin' : ''}`} />
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

        <div className="mb-4 space-y-3 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(220px,0.7fr)_auto]">
            <label className="flex min-w-0 items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 dark:border-gray-700">
              <Folder className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
              <select
                value={activeSpaceId ?? ''}
                onChange={(event) => setActiveSpaceId(event.target.value || null)}
                disabled={isLoadingSpaces}
                className="min-w-0 flex-1 bg-transparent text-sm font-medium text-gray-800 outline-none dark:text-gray-100"
              >
                <option value="">All sources</option>
                {spaces.map((space) => (
                  <option key={space.space_id} value={space.space_id}>
                    {space.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex min-w-0 items-center gap-2">
              <input
                value={newSpaceName}
                onChange={(event) => setNewSpaceName(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') void handleCreateSpace()
                }}
                placeholder="New space"
                className="min-w-0 flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
              />
              <button
                onClick={handleCreateSpace}
                disabled={!newSpaceName.trim()}
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                aria-label="Create space"
                title="Create space"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>

            <button
              onClick={handleAssignSelected}
              disabled={!activeSpaceId || selectedDocIds.length === 0 || isAssigning}
              className="flex items-center justify-center gap-2 rounded-lg bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300 dark:bg-gray-100 dark:text-gray-950 dark:hover:bg-white dark:disabled:bg-gray-700 dark:disabled:text-gray-400"
            >
              {isAssigning ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              Assign selected
            </button>
          </div>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto_minmax(180px,0.45fr)]">
            <label className="flex min-w-0 items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 dark:border-gray-700">
              <Search className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
              <input
                value={sourceQuery}
                onChange={(event) => setSourceQuery(event.target.value)}
                placeholder="Search sources"
                className="min-w-0 flex-1 bg-transparent text-sm text-gray-800 outline-none dark:text-gray-100"
              />
            </label>

            <div className="flex rounded-lg border border-gray-200 p-1 dark:border-gray-700">
              {statusOptions.map((option) => {
                const isActive = sourceStatusFilter === option.value
                return (
                  <button
                    key={option.label}
                    onClick={() => setSourceStatusFilter(option.value)}
                    className={`h-8 rounded-md px-3 text-xs font-semibold transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    }`}
                  >
                    {option.label}
                  </button>
                )
              })}
            </div>

            <label className="flex min-w-0 items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 dark:border-gray-700">
              <Tag className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
              <input
                value={tagFilterValue}
                onChange={(event) => handleTagFilterChange(event.target.value)}
                placeholder="Tags"
                className="min-w-0 flex-1 bg-transparent text-sm text-gray-800 outline-none dark:text-gray-100"
              />
            </label>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="grid grid-cols-[1fr_220px_auto_auto] gap-3 border-b border-gray-200 px-4 py-3 text-xs font-semibold uppercase text-gray-500 dark:border-gray-800 dark:text-gray-400">
            <span>Source</span>
            <span>Tags</span>
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
                <p className="mt-3 text-sm font-medium text-gray-800 dark:text-gray-200">No sources found</p>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Try another space or filter.</p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {documents.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.doc_id)
                const tags = doc.tags ?? []

                return (
                  <div
                    key={doc.doc_id}
                    className={`grid grid-cols-[1fr_220px_auto_auto] items-center gap-3 px-4 py-3 ${
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
                          {doc.summary && (
                            <p className="mt-1 line-clamp-1 text-xs text-gray-500 dark:text-gray-400">{doc.summary}</p>
                          )}
                        </div>
                      </div>
                    </button>

                    <div className="flex min-w-0 flex-wrap gap-1">
                      {tags.length > 0 ? (
                        tags.map((tag) => (
                          <span
                            key={tag}
                            className="max-w-full truncate rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                          >
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-gray-400 dark:text-gray-500">No tags</span>
                      )}
                    </div>

                    <SourceStatus status={doc.status} errorMessage={doc.error_message} />

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
            {selectedDocIds.length} sources selected · {documents.length} visible in {activeSpace ? activeSpace.name : 'all sources'}.
          </p>
        )}
      </div>
    </div>
  )
}

function SourceStatus({
  status,
  errorMessage,
}: {
  status: string
  errorMessage?: string | null
}) {
  const className =
    status === 'completed'
      ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300'
      : status === 'processing'
        ? 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
        : status === 'failed'
          ? 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
          : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'

  return (
    <div className="text-right">
      <span className={`rounded-md px-2 py-1 text-xs font-medium ${className}`}>
        {status}
      </span>
      {errorMessage && (
        <p className="mt-1 max-w-36 truncate text-xs text-red-600 dark:text-red-300" title={errorMessage}>
          {errorMessage}
        </p>
      )}
    </div>
  )
}
