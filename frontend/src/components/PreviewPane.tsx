import { useEffect, useState } from 'react'
import { AlertCircle, BookText, Loader2, RefreshCw } from 'lucide-react'
import { previewApi, type PreviewItem } from '../services/api'
import { useStore } from '../store/useStore'

function metadataEntries(metadata: Record<string, unknown>) {
  return Object.entries(metadata).filter(([, value]) => value !== null && value !== undefined && value !== '')
}

export default function PreviewPane() {
  const { previewTarget } = useStore()
  const [item, setItem] = useState<PreviewItem | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryToken, setRetryToken] = useState(0)

  useEffect(() => {
    if (!previewTarget) {
      setItem(null)
      setError(null)
      setIsLoading(false)
      return
    }

    let isMounted = true
    setIsLoading(true)
    setError(null)

    previewApi.get(previewTarget.type, previewTarget.id)
      .then((data) => {
        if (isMounted) setItem(data)
      })
      .catch((previewError) => {
        console.error('Failed to load preview:', previewError)
        if (isMounted) {
          setItem(null)
          setError('Preview unavailable')
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [previewTarget, retryToken])

  if (!previewTarget) {
    return (
      <div data-testid="preview-pane" className="flex h-full items-center justify-center text-center">
        <div>
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-lg bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
            <BookText className="h-5 w-5" />
          </div>
          <p className="mt-3 text-sm font-medium text-gray-800 dark:text-gray-200">Select an item to preview</p>
          <p className="mt-1 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
            Choose a document, wiki page, note, or output from the workspace.
          </p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div data-testid="preview-pane" className="rounded-lg border border-[#e2e1de] bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading preview
        </div>
      </div>
    )
  }

  if (error || !item) {
    return (
      <div data-testid="preview-pane" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-900 shadow-sm dark:border-red-900 dark:bg-red-950 dark:text-red-100">
        <div className="flex items-start gap-2">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold">Preview unavailable</p>
            <p className="mt-1 text-xs">The selected item could not be loaded.</p>
            <button
              type="button"
              onClick={() => setRetryToken((value) => value + 1)}
              className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-red-200 bg-white px-2 py-1 text-xs font-semibold text-red-900 hover:bg-red-100 dark:border-red-800 dark:bg-red-950 dark:hover:bg-red-900"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry preview
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <article data-testid="preview-pane" className="flex min-h-0 flex-col rounded-lg border border-[#e2e1de] bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="border-b border-[#e2e1de] p-4 dark:border-gray-800">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.type}</p>
        <h3 className="mt-1 text-base font-semibold text-slate-950 dark:text-slate-100">{item.title}</h3>
      </div>

      {metadataEntries(item.metadata).length > 0 && (
        <dl className="grid grid-cols-2 gap-2 border-b border-[#e2e1de] p-4 text-xs dark:border-gray-800">
          {metadataEntries(item.metadata).map(([key, value]) => (
            <div key={key} className="min-w-0 rounded-md bg-[#f5f4f3] px-2 py-1.5 dark:bg-gray-800">
              <dt className="truncate font-semibold text-slate-500">{key}</dt>
              <dd className="mt-0.5 truncate text-slate-800 dark:text-slate-200">{String(value)}</dd>
            </div>
          ))}
        </dl>
      )}

      <pre
        data-testid="preview-content"
        className="max-h-[28rem] min-h-0 overflow-y-auto whitespace-pre-wrap break-words p-4 text-sm leading-relaxed text-slate-800 dark:text-slate-200"
      >
        {item.content_preview || 'No preview content available.'}
      </pre>

      {item.links.length > 0 && (
        <div className="border-t border-[#e2e1de] p-4 dark:border-gray-800">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Links</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {item.links.map((link) => (
              <span key={`${link.type}-${link.id}`} className="rounded-md border border-[#e2e1de] bg-[#f5f4f3] px-2 py-1 text-xs text-slate-700 dark:border-gray-700 dark:bg-gray-800 dark:text-slate-200">
                {link.title}
              </span>
            ))}
          </div>
        </div>
      )}
    </article>
  )
}
