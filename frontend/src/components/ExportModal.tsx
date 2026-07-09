import { useState } from 'react'
import { X, Download, FileText, MessageSquare, CheckCircle } from 'lucide-react'
import { useStore } from '../store/useStore'

const API_BASE_URL = 'http://localhost:8000'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function ExportModal({ isOpen, onClose }: ExportModalProps) {
  const [exportType, setExportType] = useState<'conversation' | 'notes' | 'both'>('conversation')
  const [format, setFormat] = useState<'markdown' | 'pdf'>('markdown')
  const [isExporting, setIsExporting] = useState(false)
  const [exportSuccess, setExportSuccess] = useState(false)

  const { messages, conversationId } = useStore()

  const handleExport = async () => {
    setIsExporting(true)
    setExportSuccess(false)

    try {
      if (exportType === 'conversation' || exportType === 'both') {
        await exportConversation()
      }

      if (exportType === 'notes' || exportType === 'both') {
        await exportNotes()
      }

      setExportSuccess(true)
      setTimeout(() => {
        setExportSuccess(false)
        onClose()
      }, 2000)
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

    // 生成 Markdown 内容
    let markdown = `# Conversation Export\n\n`
    markdown += `**Exported on:** ${new Date().toLocaleString()}\n\n`
    markdown += `---\n\n`

    messages.forEach((message, index) => {
      markdown += `## ${message.role === 'user' ? 'Question' : 'Answer'} ${Math.floor(index / 2) + 1}\n\n`
      markdown += `${message.content}\n\n`

      if (message.citations && message.citations.length > 0) {
        markdown += `### Sources\n\n`
        message.citations.forEach((citation) => {
          markdown += `- [${citation.number}] ${citation.doc_name}`
          if (citation.page) markdown += ` (Page ${citation.page})`
          markdown += ` - ${Math.round(citation.relevance_score * 100)}% relevance\n`
        })
        markdown += `\n`
      }

      markdown += `---\n\n`
    })

    // 下载文件
    downloadFile(markdown, `conversation-${conversationId || Date.now()}.md`, 'text/markdown')
  }

  const exportNotes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notes/list`)
      const data = await response.json()
      const notes = data.notes || []

      if (notes.length === 0) {
        alert('No notes to export')
        return
      }

      // 生成 Markdown 内容
      let markdown = `# Notes Export\n\n`
      markdown += `**Exported on:** ${new Date().toLocaleString()}\n\n`
      markdown += `**Total Notes:** ${notes.length}\n\n`
      markdown += `---\n\n`

      notes.forEach((note: any, index: number) => {
        markdown += `# ${note.title}\n\n`
        markdown += `**Created:** ${new Date(note.created_at).toLocaleString()}\n`
        markdown += `**Updated:** ${new Date(note.updated_at).toLocaleString()}\n\n`
        markdown += `${note.content}\n\n`

        if (index < notes.length - 1) {
          markdown += `---\n\n`
        }
      })

      // 下载文件
      downloadFile(markdown, `notes-export-${Date.now()}.md`, 'text/markdown')
    } catch (error) {
      console.error('Failed to export notes:', error)
      throw error
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
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">Export</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Export Type Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              What to export
            </label>
            <div className="space-y-2">
              <button
                onClick={() => setExportType('conversation')}
                className={`w-full flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                  exportType === 'conversation'
                    ? 'bg-blue-50 border-blue-400'
                    : 'bg-white border-gray-200 hover:border-blue-300'
                }`}
              >
                <MessageSquare className="w-5 h-5 text-blue-600" />
                <div className="flex-1 text-left">
                  <p className="font-semibold text-sm text-gray-900">Current Conversation</p>
                  <p className="text-xs text-gray-500">{messages.length} messages</p>
                </div>
                {exportType === 'conversation' && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </button>

              <button
                onClick={() => setExportType('notes')}
                className={`w-full flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                  exportType === 'notes'
                    ? 'bg-blue-50 border-blue-400'
                    : 'bg-white border-gray-200 hover:border-blue-300'
                }`}
              >
                <FileText className="w-5 h-5 text-green-600" />
                <div className="flex-1 text-left">
                  <p className="font-semibold text-sm text-gray-900">All Notes</p>
                  <p className="text-xs text-gray-500">Export all saved notes</p>
                </div>
                {exportType === 'notes' && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </button>

              <button
                onClick={() => setExportType('both')}
                className={`w-full flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                  exportType === 'both'
                    ? 'bg-blue-50 border-blue-400'
                    : 'bg-white border-gray-200 hover:border-blue-300'
                }`}
              >
                <Download className="w-5 h-5 text-purple-600" />
                <div className="flex-1 text-left">
                  <p className="font-semibold text-sm text-gray-900">Everything</p>
                  <p className="text-xs text-gray-500">Conversation + all notes</p>
                </div>
                {exportType === 'both' && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </button>
            </div>
          </div>

          {/* Format Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Format
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setFormat('markdown')}
                className={`flex-1 p-3 rounded-xl border-2 transition-all ${
                  format === 'markdown'
                    ? 'bg-blue-50 border-blue-400 text-blue-900'
                    : 'bg-white border-gray-200 hover:border-blue-300 text-gray-700'
                }`}
              >
                <p className="font-semibold text-sm">Markdown</p>
                <p className="text-xs opacity-70">.md</p>
              </button>
              <button
                onClick={() => setFormat('pdf')}
                disabled
                className="flex-1 p-3 rounded-xl border-2 bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed"
              >
                <p className="font-semibold text-sm">PDF</p>
                <p className="text-xs opacity-70">Coming soon</p>
              </button>
            </div>
          </div>

          {/* Success Message */}
          {exportSuccess && (
            <div className="p-4 bg-green-50 border-2 border-green-400 rounded-xl flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <p className="text-sm font-medium text-green-900">Export successful!</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-100 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isExporting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Exporting...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Export</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
