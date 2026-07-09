import { useEffect } from 'react'
import { FileText, Plus, ChevronLeft, ChevronRight, X, CheckCircle2, Loader2 } from 'lucide-react'
import { useStore } from '../store/useStore'
import { documentApi } from '../services/api'

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
  onUploadClick: () => void
}

export default function Sidebar({ isCollapsed, onToggle, onUploadClick }: SidebarProps) {
  const { documents, selectedDocIds, setDocuments, toggleDocumentSelection, removeDocument, addToast } = useStore()

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const data = await documentApi.list()
      setDocuments(data.documents)
    } catch (error) {
      console.error('Failed to load documents:', error)
      addToast('Failed to load sources', 'error')
    }
  }

  const handleDelete = async (docId: string) => {
    try {
      await documentApi.delete(docId)
      removeDocument(docId)
      addToast('Source deleted', 'success')
    } catch (error) {
      console.error('Failed to delete document:', error)
      addToast('Failed to delete source', 'error')
    }
  }

  if (isCollapsed) {
    return (
      <div className="w-14 border-r border-gray-200 dark:border-gray-800 flex flex-col items-center py-4 bg-gray-50 dark:bg-gray-900">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg transition-colors"
          aria-label="Expand sidebar"
        >
          <ChevronRight className="w-5 h-5 text-gray-500 dark:text-gray-400" />
        </button>
      </div>
    )
  }

  return (
    <div className="w-72 border-r border-gray-200 dark:border-gray-800 flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="p-5 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sources</h2>
          <button
            onClick={onToggle}
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          </button>
        </div>
        <button
          onClick={onUploadClick}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md"
        >
          <Plus className="w-4 h-4" strokeWidth={2.5} />
          <span className="text-sm font-medium">Add source</span>
        </button>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-4">
        {documents.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-blue-600" strokeWidth={1.5} />
            </div>
            <p className="text-sm font-semibold text-gray-800 mb-2">No sources yet</p>
            <p className="text-xs text-gray-500 leading-relaxed px-4">Upload documents to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.doc_id)
              return (
                <div
                  key={doc.doc_id}
                  className={`group relative p-4 rounded-xl border-2 transition-all cursor-pointer ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-lg'
                  }`}
                  onClick={() => toggleDocumentSelection(doc.doc_id)}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`p-2.5 rounded-lg ${isSelected ? 'bg-blue-200' : 'bg-gray-100'} transition-colors`}>
                      <FileText className={`w-5 h-5 ${isSelected ? 'text-blue-700' : 'text-gray-600'}`} strokeWidth={2} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 truncate mb-1">{doc.filename}</p>

                      {/* 文档摘要 */}
                      {doc.summary && doc.status === 'completed' && (
                        <p className="text-xs text-gray-600 leading-relaxed mb-2 line-clamp-2">
                          {doc.summary}
                        </p>
                      )}

                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold ${
                          doc.status === 'completed' ? 'bg-green-100 text-green-800' :
                          doc.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {doc.status === 'completed' ? (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          ) : doc.status === 'processing' ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : null}
                          <span>{doc.status}</span>
                        </span>
                        <span className="text-xs text-gray-600 font-medium">{doc.total_chunks} chunks</span>
                      </div>
                    </div>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation()
                        await handleDelete(doc.doc_id)
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 rounded-lg transition-all"
                      aria-label="Remove document"
                    >
                      <X className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      {documents.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-white">
          <p className="text-xs text-gray-600 font-medium">
            <span className="text-blue-600 font-bold">{selectedDocIds.length}</span> of {documents.length} sources selected
          </p>
        </div>
      )}
    </div>
  )
}
