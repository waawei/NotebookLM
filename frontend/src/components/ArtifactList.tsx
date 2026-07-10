import { useEffect, useState } from 'react'
import { Eye, FileText, Loader2 } from 'lucide-react'
import { outputApi, type OutputItem } from '../services/api'
import { useStore } from '../store/useStore'
import ArtifactLifecycleMenu from './ArtifactLifecycleMenu'

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Unknown date'
  return date.toLocaleDateString()
}

interface ArtifactListProps {
  includeArchived?: boolean
}

export default function ArtifactList({ includeArchived = false }: ArtifactListProps) {
  const [outputs, setOutputs] = useState<OutputItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { artifactRefreshToken, setPreviewTarget, bumpArtifactRefreshToken } = useStore()

  const openPreview = (output: OutputItem) => {
    setPreviewTarget({ type: 'output', id: output.output_id, title: output.title })
  }

  useEffect(() => {
    let isMounted = true
    setIsLoading(true)
    outputApi.list(undefined, includeArchived)
      .then((data) => {
        if (isMounted) setOutputs(data.outputs || [])
      })
      .catch((error) => {
        console.error('Failed to load artifacts:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [artifactRefreshToken, includeArchived])

  const handleExport = async (output: OutputItem) => {
    try {
      const exported = await outputApi.export(output.output_id)
      downloadFile(exported.content, exported.filename, exported.content_type)
    } catch (error) {
      console.error('Failed to export artifact:', error)
    }
  }

  const handleArchive = async (output: OutputItem) => {
    try {
      await outputApi.archive(output.output_id)
      bumpArtifactRefreshToken()
    } catch (error) {
      console.error('Failed to archive artifact:', error)
    }
  }

  const handleRestore = async (output: OutputItem) => {
    try {
      await outputApi.restore(output.output_id)
      bumpArtifactRefreshToken()
    } catch (error) {
      console.error('Failed to restore artifact:', error)
    }
  }

  return (
    <section data-testid="artifact-list" aria-labelledby="artifact-list-heading" className="space-y-2">
      <h3 id="artifact-list-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Artifacts
      </h3>

      {isLoading ? (
        <div className="flex items-center gap-2 rounded-lg border border-[#e2e1de] bg-white p-3 text-xs text-slate-500 dark:border-gray-800 dark:bg-gray-900">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading artifacts
        </div>
      ) : outputs.length === 0 ? (
        <div className="rounded-lg border border-[#e2e1de] bg-white p-3 text-xs text-slate-500 dark:border-gray-800 dark:bg-gray-900">
          No artifacts yet
        </div>
      ) : (
        <div className="space-y-2">
          {outputs.map((output) => {
            const sourceLabel = `${output.source_doc_ids.length} ${output.source_doc_ids.length === 1 ? 'source' : 'sources'}`
            return (
              <article
                key={output.output_id}
                className="w-full rounded-lg border border-[#e2e1de] bg-white p-3 text-left shadow-sm transition-colors hover:border-blue-200 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-900"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-[#f5f4f3] text-slate-600 dark:bg-gray-800 dark:text-gray-300">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="truncate text-sm font-semibold text-slate-950 dark:text-slate-100">{output.title}</p>
                      <span className="rounded-md border border-[#e2e1de] bg-[#f5f4f3] px-2 py-0.5 text-[11px] font-semibold text-slate-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
                        {output.kind}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      <span>{sourceLabel}</span>
                      <span> · {formatDate(output.created_at)}</span>
                    </p>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-1">
                    <button
                      type="button"
                      onClick={() => openPreview(output)}
                      className="flex h-8 w-8 items-center justify-center rounded-md border border-blue-100 bg-blue-50 text-blue-700 hover:bg-blue-100 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-300"
                      aria-label={`Preview ${output.title}`}
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <ArtifactLifecycleMenu
                      output={output}
                      onPreview={() => openPreview(output)}
                      onExport={() => void handleExport(output)}
                      onArchive={() => void handleArchive(output)}
                      onRestore={() => void handleRestore(output)}
                    />
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

function downloadFile(content: string, filename: string, mimeType: string) {
  if (typeof document === 'undefined' || typeof URL === 'undefined' || !URL.createObjectURL) {
    return
  }

  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
