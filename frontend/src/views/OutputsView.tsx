import { useEffect, useMemo, useState } from 'react'
import { Archive, Download, FileText, Loader2, RefreshCw, RotateCcw, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { outputApi, type OutputItem } from '../services/api'
import type { AppModule } from '../store/useStore'
import { useStore } from '../store/useStore'

interface OutputsViewProps {
  onModuleChange: (module: AppModule) => void
}

const outputKinds = [
  { value: 'summary', label: 'Summary' },
  { value: 'outline', label: 'Outline' },
  { value: 'review_cards', label: 'Review Cards' },
  { value: 'quiz', label: 'Quiz' },
  { value: 'paper_plan', label: 'Paper Plan' },
]

export default function OutputsView({ onModuleChange }: OutputsViewProps) {
  const { selectedDocIds, addToast } = useStore()
  const [outputs, setOutputs] = useState<OutputItem[]>([])
  const [selectedOutputId, setSelectedOutputId] = useState<string | null>(null)
  const [selectedKind, setSelectedKind] = useState('summary')
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showArchived, setShowArchived] = useState(false)

  const selectedOutput = useMemo(
    () => outputs.find((output) => output.output_id === selectedOutputId) || outputs[0] || null,
    [outputs, selectedOutputId],
  )

  useEffect(() => {
    void loadOutputs(false)
  }, [])

  const loadOutputs = async (includeArchived = showArchived) => {
    setIsLoading(true)
    try {
      const data = await outputApi.list(undefined, includeArchived)
      setOutputs(data.outputs)
      setSelectedOutputId((current) => (
        current && data.outputs.some((output) => output.output_id === current)
          ? current
          : data.outputs[0]?.output_id || null
      ))
    } catch (error) {
      console.error('Failed to load outputs:', error)
      addToast('Failed to load outputs', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (selectedDocIds.length === 0) {
      addToast('Select at least one source first', 'error')
      return
    }

    setIsGenerating(true)
    try {
      const output = await outputApi.generate({
        kind: selectedKind,
        source_doc_ids: selectedDocIds,
      })
      setShowArchived(false)
      setOutputs((current) => [output, ...current])
      setSelectedOutputId(output.output_id)
      addToast('Output generated', 'success')
    } catch (error) {
      console.error('Failed to generate output:', error)
      addToast('Failed to generate output', 'error')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleArchive = async (outputId: string) => {
    try {
      await outputApi.archive(outputId)
      await loadOutputs(showArchived)
      addToast('Output archived', 'success')
    } catch (error) {
      console.error('Failed to archive output:', error)
      addToast('Failed to archive output', 'error')
    }
  }

  const handleRestore = async (outputId: string) => {
    try {
      await outputApi.restore(outputId)
      await loadOutputs(showArchived)
      addToast('Output restored', 'success')
    } catch (error) {
      console.error('Failed to restore output:', error)
      addToast('Failed to restore output', 'error')
    }
  }

  const handleExport = async (outputId: string) => {
    try {
      const exported = await outputApi.export(outputId)
      downloadFile(exported.content, exported.filename, exported.content_type)
      addToast('Output exported', 'success')
    } catch (error) {
      console.error('Failed to export output:', error)
      addToast('Failed to export output', 'error')
    }
  }

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    if (typeof URL === 'undefined' || !URL.createObjectURL) return
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

  const switchArchivedFilter = (includeArchived: boolean) => {
    setShowArchived(includeArchived)
    setSelectedOutputId(null)
    void loadOutputs(includeArchived)
  }

  return (
    <div className="grid h-full grid-cols-[minmax(280px,360px)_1fr] bg-gray-100 dark:bg-gray-950">
      <aside className="min-h-0 border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="border-b border-gray-200 p-4 dark:border-gray-800">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Outputs</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">{outputs.length} generated artifacts</p>
            </div>
            <button
              onClick={() => void loadOutputs(showArchived)}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
              title="Refresh outputs"
              aria-label="Refresh outputs"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-3">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">Kind</span>
              <select
                value={selectedKind}
                onChange={(event) => setSelectedKind(event.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
              >
                {outputKinds.map((kind) => (
                  <option key={kind.value} value={kind.value}>
                    {kind.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {selectedDocIds.length} selected sources
            </div>

            <div className="grid grid-cols-2 gap-1 rounded-lg bg-gray-50 p-1 text-xs dark:bg-gray-800">
              {[
                { label: 'Active', value: false },
                { label: 'Archived', value: true },
              ].map((filter) => (
                <button
                  key={filter.label}
                  type="button"
                  onClick={() => switchArchivedFilter(filter.value)}
                  className={`rounded-md px-2 py-1.5 font-semibold transition-colors ${
                    showArchived === filter.value
                      ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-100 dark:bg-blue-950 dark:text-blue-200 dark:ring-blue-900'
                      : 'text-gray-500 hover:bg-white hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-900 dark:hover:text-gray-100'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating || selectedDocIds.length === 0 || showArchived}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700"
            >
              {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {showArchived ? 'Archived view' : 'Generate'}
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          {isLoading && outputs.length === 0 ? (
            <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading outputs
            </div>
          ) : outputs.length === 0 ? (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-700" />
              <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">No outputs yet</p>
              <button
                onClick={() => onModuleChange('workbench')}
                className="mt-3 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                Select sources
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {outputs.map((output) => {
                const isSelected = selectedOutput?.output_id === output.output_id
                return (
                  <button
                    key={output.output_id}
                    onClick={() => setSelectedOutputId(output.output_id)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      isSelected
                        ? 'border-blue-400 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
                        : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:bg-gray-800'
                    }`}
                  >
                    <p className="truncate text-sm font-medium text-gray-950 dark:text-gray-100">{output.title}</p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {output.kind} - {output.source_doc_ids.length} sources{output.status === 'archived' ? ' - archived' : ''}
                    </p>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </aside>

      <main className="min-w-0 overflow-y-auto p-6">
        {selectedOutput ? (
          <article className="mx-auto max-w-4xl rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-5 flex items-start justify-between gap-3 border-b border-gray-100 pb-4 dark:border-gray-800">
              <div className="min-w-0">
                <h1 className="truncate text-xl font-semibold text-gray-950 dark:text-gray-100">{selectedOutput.title}</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {selectedOutput.source_doc_ids.length} sources - Updated {new Date(selectedOutput.updated_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleExport(selectedOutput.output_id)}
                  className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-50 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-blue-300"
                  title="Export output"
                  aria-label="Export output"
                >
                  <Download className="h-4 w-4" />
                </button>
                {selectedOutput.status === 'archived' ? (
                  <button
                    onClick={() => handleRestore(selectedOutput.output_id)}
                    className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 hover:bg-blue-50 hover:text-blue-700 dark:text-gray-400 dark:hover:bg-blue-950 dark:hover:text-blue-300"
                    title="Restore output"
                    aria-label="Restore output"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => handleArchive(selectedOutput.output_id)}
                    className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
                    title="Archive output"
                    aria-label="Archive output"
                  >
                    <Archive className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{selectedOutput.content}</ReactMarkdown>
            </div>
          </article>
        ) : (
          <div className="flex h-full items-center justify-center text-center">
            <div>
              <FileText className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-700" />
              <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">Generate or select an output</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
