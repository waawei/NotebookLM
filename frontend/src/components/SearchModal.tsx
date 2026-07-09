import { useState, useEffect } from 'react'
import { X, Search, FileText, MessageSquare, File } from 'lucide-react'
import { useStore } from '../store/useStore'
import ReactMarkdown from 'react-markdown'
import { noteApi } from '../services/api'

interface Note {
  note_id: string
  title: string
  content: string
  doc_ids: string[]
  created_at: string
  updated_at: string
}

interface SearchResult {
  type: 'message' | 'note' | 'document'
  id: string
  title: string
  content: string
  preview: string
  timestamp?: string
}

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null)

  const { messages, documents } = useStore()

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }

    const timeoutId = setTimeout(() => {
      performSearch()
    }, 300) // 300ms debounce

    return () => clearTimeout(timeoutId)
  }, [query, messages, documents])

  const performSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    try {
      const allResults: SearchResult[] = []

      // 1. 搜索对话消息
      messages.forEach((message, index) => {
        if (message.content.toLowerCase().includes(query.toLowerCase())) {
          allResults.push({
            type: 'message',
            id: `message-${index}`,
            title: message.role === 'user' ? 'Your Question' : 'Assistant Response',
            content: message.content,
            preview: highlightMatch(message.content.substring(0, 200), query),
            timestamp: undefined
          })
        }
      })

      // 2. 搜索笔记
      const notesData = await noteApi.list()
      const notes: Note[] = notesData.notes || []

      notes.forEach((note) => {
        const titleMatch = note.title.toLowerCase().includes(query.toLowerCase())
        const contentMatch = note.content.toLowerCase().includes(query.toLowerCase())

        if (titleMatch || contentMatch) {
          allResults.push({
            type: 'note',
            id: note.note_id,
            title: note.title,
            content: note.content,
            preview: highlightMatch(
              contentMatch ? note.content.substring(0, 200) : note.title,
              query
            ),
            timestamp: note.updated_at
          })
        }
      })

      // 3. 搜索文档（仅搜索文档名称和摘要）
      documents.forEach((doc) => {
        const nameMatch = doc.filename.toLowerCase().includes(query.toLowerCase())
        const summaryMatch = doc.summary?.toLowerCase().includes(query.toLowerCase())

        if (nameMatch || summaryMatch) {
          allResults.push({
            type: 'document',
            id: doc.doc_id,
            title: doc.filename,
            content: doc.summary || 'No summary available',
            preview: highlightMatch(
              summaryMatch ? (doc.summary || '') : doc.filename,
              query
            ),
            timestamp: doc.upload_time
          })
        }
      })

      setResults(allResults)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const highlightMatch = (text: string, query: string): string => {
    const index = text.toLowerCase().indexOf(query.toLowerCase())
    if (index === -1) return text

    const start = Math.max(0, index - 50)
    const end = Math.min(text.length, index + query.length + 100)
    let preview = text.substring(start, end)

    if (start > 0) preview = '...' + preview
    if (end < text.length) preview = preview + '...'

    return preview
  }

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'message':
        return <MessageSquare className="w-4 h-4 text-blue-600" />
      case 'note':
        return <FileText className="w-4 h-4 text-green-600" />
      case 'document':
        return <File className="w-4 h-4 text-purple-600" />
      default:
        return <Search className="w-4 h-4 text-gray-600" />
    }
  }

  const getResultTypeLabel = (type: string) => {
    switch (type) {
      case 'message':
        return 'Conversation'
      case 'note':
        return 'Note'
      case 'document':
        return 'Document'
      default:
        return 'Unknown'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-4xl h-[80vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900">Search</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search conversations, notes, and documents..."
              className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-xl focus:border-blue-400 outline-none text-sm"
              autoFocus
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Results List */}
          <div className="w-2/5 border-r border-gray-200 overflow-y-auto bg-gray-50">
            {isSearching ? (
              <div className="p-8 text-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-3" />
                <p className="text-sm text-gray-600">Searching...</p>
              </div>
            ) : results.length === 0 ? (
              <div className="p-8 text-center">
                {query.trim() ? (
                  <>
                    <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-sm text-gray-500">No results found</p>
                  </>
                ) : (
                  <>
                    <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-sm text-gray-500">Start typing to search</p>
                  </>
                )}
              </div>
            ) : (
              <div className="p-3 space-y-2">
                {results.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => setSelectedResult(result)}
                    className={`w-full text-left p-3 rounded-xl transition-all ${
                      selectedResult?.id === result.id
                        ? 'bg-blue-50 border-2 border-blue-400'
                        : 'bg-white border-2 border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {getResultIcon(result.type)}
                      <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        {getResultTypeLabel(result.type)}
                      </span>
                    </div>
                    <p className="font-semibold text-sm text-gray-900 mb-1 line-clamp-1">
                      {result.title}
                    </p>
                    <p className="text-xs text-gray-600 line-clamp-2">
                      {result.preview}
                    </p>
                    {result.timestamp && (
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(result.timestamp).toLocaleDateString()}
                      </p>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Result Detail */}
          <div className="flex-1 overflow-y-auto p-6 bg-white">
            {selectedResult ? (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  {getResultIcon(selectedResult.type)}
                  <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {getResultTypeLabel(selectedResult.type)}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  {selectedResult.title}
                </h3>
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{selectedResult.content}</ReactMarkdown>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 font-medium">Select a result to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
