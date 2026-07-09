import { useEffect, useMemo, useState } from 'react'
import { FileText, Loader2, RefreshCw, Sparkles, Trash2 } from 'lucide-react'
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

  const selectedOutput = useMemo(
    () => outputs.find((output) => output.output_id === selectedOutputId) || outputs[0] || null,
    [outputs, selectedOutputId],
  )

  useEffect(() => {
    void loadOutputs()
  }, [])

  const loadOutputs = async () => {
    setIsLoading(true)
    try {
      const data = await outputApi.list()
      setOutputs(data.outputs)
      setSelectedOutputId((current) => current || data.outputs[0]?.output_id || null)
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

  const handleDelete = async (outputId: string) => {
    try {
      await outputApi.delete(outputId)
      setOutputs((current) => current.filter((output) => output.output_id !== outputId))
      setSelectedOutputId(null)
      addToast('Output deleted', 'success')
    } catch (error) {
      console.error('Failed to delete output:', error)
      addToast('Failed to delete output', 'error')
    }
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
              onClick={loadOutputs}
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

            <button
              onClick={handleGenerate}
              disabled={isGenerating || selectedDocIds.length === 0}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700"
            >
              {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Generate
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
                      {output.kind} · {output.source_doc_ids.length} sources
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
                  {selectedOutput.source_doc_ids.length} sources · Updated {new Date(selectedOutput.updated_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => handleDelete(selectedOutput.output_id)}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 hover:bg-red-50 hover:text-red-600 dark:text-gray-400 dark:hover:bg-red-950 dark:hover:text-red-300"
                title="Delete output"
                aria-label="Delete output"
              >
                <Trash2 className="h-4 w-4" />
              </button>
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
