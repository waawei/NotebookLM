import { useState } from 'react'
import {
  BookOpenText,
  CheckCircle,
  Download,
  FileText,
  MessageSquare,
  Sparkles,
  X,
} from 'lucide-react'
import { noteApi, outputApi, wikiApi } from '../services/api'
import { useStore } from '../store/useStore'

type ExportType = 'conversation' | 'notes' | 'outputs' | 'wiki' | 'everything'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
}

const exportOptions: Array<{
  key: ExportType
  title: string
  subtitle: string
  icon: typeof Download
  iconClass: string
}> = [
  {
    key: 'conversation',
    title: 'Current Conversation',
    subtitle: 'Messages and cited sources',
    icon: MessageSquare,
    iconClass: 'text-blue-600',
  },
  {
    key: 'notes',
    title: 'All Notes',
    subtitle: 'Saved notes and note content',
    icon: FileText,
    iconClass: 'text-green-600',
  },
  {
    key: 'outputs',
    title: 'Generated Outputs',
    subtitle: 'Summaries, outlines, quizzes, and plans',
    icon: Sparkles,
    iconClass: 'text-amber-600',
  },
  {
    key: 'wiki',
    title: 'Wiki Pages',
    subtitle: 'Persisted Wiki markdown pages',
    icon: BookOpenText,
    iconClass: 'text-violet-600',
  },
  {
    key: 'everything',
    title: 'Everything',
    subtitle: 'Conversation, notes, outputs, and Wiki pages',
    icon: Download,
    iconClass: 'text-gray-700 dark:text-gray-200',
  },
]

export default function ExportModal({ isOpen, onClose }: ExportModalProps) {
  const [exportType, setExportType] = useState<ExportType>('conversation')
  const [format, setFormat] = useState<'markdown' | 'pdf'>('markdown')
  const [isExporting, setIsExporting] = useState(false)
  const [exportSuccess, setExportSuccess] = useState(false)

  const { messages, conversationId } = useStore()

  const handleExport = async () => {
    setIsExporting(true)
    setExportSuccess(false)

    try {
      if (exportType === 'conversation' || exportType === 'everything') {
        await exportConversation()
      }

      if (exportType === 'notes' || exportType === 'everything') {
        await exportNotes()
      }

      if (exportType === 'outputs' || exportType === 'everything') {
        await exportOutputs()
      }

      if (exportType === 'wiki' || exportType === 'everything') {
        await exportWikiPages()
      }

      setExportSuccess(true)
      setTimeout(() => {
        setExportSuccess(false)
        onClose()
      }, 1600)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const exportConversation = async () => {
    if (messages.length === 0) {
      alert('No conversation to export')
      return
    }

    let markdown = '# Conversation Export\n\n'
    markdown += `**Exported on:** ${new Date().toLocaleString()}\n\n`
    markdown += '---\n\n'

    messages.forEach((message, index) => {
      markdown += `## ${message.role === 'user' ? 'Question' : 'Answer'} ${Math.floor(index / 2) + 1}\n\n`
      markdown += `${message.content}\n\n`

      if (message.citations && message.citations.length > 0) {
        markdown += '### Sources\n\n'
        message.citations.forEach((citation) => {
          markdown += `- [${citation.number}] ${citation.doc_name}`
          if (citation.page) markdown += ` (Page ${citation.page})`
          markdown += ` - ${Math.round(citation.relevance_score * 100)}% relevance\n`
        })
        markdown += '\n'
      }

      markdown += '---\n\n'
    })

    downloadFile(markdown, `conversation-${conversationId || Date.now()}.md`, 'text/markdown')
  }

  const exportNotes = async () => {
    const data = await noteApi.list()
    const notes = data.notes || []

    if (notes.length === 0) {
      alert('No notes to export')
      return
    }

    let markdown = '# Notes Export\n\n'
    markdown += `**Exported on:** ${new Date().toLocaleString()}\n\n`
    markdown += `**Total Notes:** ${notes.length}\n\n`
    markdown += '---\n\n'

    notes.forEach((note, index) => {
      markdown += `# ${note.title}\n\n`
      markdown += `**Created:** ${new Date(note.created_at).toLocaleString()}\n`
      markdown += `**Updated:** ${new Date(note.updated_at).toLocaleString()}\n\n`
      markdown += `${note.content}\n\n`

      if (index < notes.length - 1) {
        markdown += '---\n\n'
      }
    })

    downloadFile(markdown, `notes-export-${Date.now()}.md`, 'text/markdown')
  }

  const exportOutputs = async () => {
    const data = await outputApi.list()
    const outputs = data.outputs || []

    if (outputs.length === 0) {
      alert('No generated outputs to export')
      return
    }

    for (const output of outputs) {
      const exported = await outputApi.export(output.output_id)
      downloadFile(exported.content, exported.filename, exported.content_type)
    }
  }

  const exportWikiPages = async () => {
    const data = await wikiApi.list()
    const pages = data.pages || []

    if (pages.length === 0) {
      alert('No Wiki pages to export')
      return
    }

    for (const page of pages) {
      const exported = await wikiApi.export(page.page_id)
      downloadFile(exported.content, exported.filename, exported.content_type)
    }
  }

  const downloadFile = (content: string, filename: string, mimeType: string) => {
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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md overflow-hidden rounded-lg bg-white shadow-2xl dark:bg-gray-900">
        <div className="border-b border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Export</h2>
            <button
              onClick={onClose}
              className="rounded-lg p-2 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="Close export modal"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        </div>

        <div className="space-y-6 p-6">
          <div>
            <label className="mb-3 block text-sm font-semibold text-gray-700 dark:text-gray-200">
              What to export
            </label>
            <div className="space-y-2">
              {exportOptions.map((option) => {
                const Icon = option.icon
                const isSelected = exportType === option.key
                return (
                  <button
                    key={option.key}
                    onClick={() => setExportType(option.key)}
                    className={`flex w-full items-center gap-3 rounded-lg border p-4 transition-colors ${
                      isSelected
                        ? 'border-blue-400 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
                        : 'border-gray-200 bg-white hover:border-blue-300 dark:border-gray-700 dark:bg-gray-950 dark:hover:border-blue-700'
                    }`}
                  >
                    <Icon className={`h-5 w-5 ${option.iconClass}`} />
                    <div className="min-w-0 flex-1 text-left">
                      <p className="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {option.title}
                      </p>
                      <p className="truncate text-xs text-gray-500 dark:text-gray-400">{option.subtitle}</p>
                    </div>
                    {isSelected && <CheckCircle className="h-5 w-5 text-blue-600" />}
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="mb-3 block text-sm font-semibold text-gray-700 dark:text-gray-200">
              Format
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setFormat('markdown')}
                className={`flex-1 rounded-lg border p-3 transition-colors ${
                  format === 'markdown'
                    ? 'border-blue-400 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-100'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-200'
                }`}
              >
                <p className="text-sm font-semibold">Markdown</p>
                <p className="text-xs opacity-70">.md</p>
              </button>
              <button
                onClick={() => setFormat('pdf')}
                disabled
                className="flex-1 cursor-not-allowed rounded-lg border border-gray-200 bg-gray-100 p-3 text-gray-400 dark:border-gray-700 dark:bg-gray-800"
              >
                <p className="text-sm font-semibold">PDF</p>
                <p className="text-xs opacity-70">Coming soon</p>
              </button>
            </div>
          </div>

          {exportSuccess && (
            <div className="flex items-center gap-3 rounded-lg border border-green-300 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-300" />
              <p className="text-sm font-medium text-green-900 dark:text-green-100">Export successful</p>
            </div>
          )}
        </div>

        <div className="flex gap-3 border-t border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-950">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isExporting ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Exporting</span>
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                <span>Export</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
