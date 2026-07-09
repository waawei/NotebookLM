import { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'
import { documentApi } from '../services/api'
import { FileText, Trash2, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'

export default function DocumentList() {
  const { documents, setDocuments, selectedDocIds, toggleDocumentSelection, removeDocument } = useStore()
  const [isLoading, setIsLoading] = useState(false)

  // 加载文档列表
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setIsLoading(true)
    try {
      const data = await documentApi.list()
      setDocuments(data.documents)
    } catch (error) {
      console.error('加载文档列表失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (docId: string) => {
    if (!confirm('确定删除这个文档吗？')) return

    try {
      await documentApi.delete(docId)
      removeDocument(docId)
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除失败，请重试')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Loader2 className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'processing':
        return '处理中'
      case 'failed':
        return '失败'
      default:
        return '等待中'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">文档列表</h2>
        {documents.length > 0 && (
          <span className="text-sm text-gray-500">{documents.length} 个文档</span>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
          <p className="text-sm">还没有上传文档</p>
          <p className="text-xs mt-1">点击右上角"上传文档"开始</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.doc_id}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedDocIds.includes(doc.doc_id)
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-white border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => toggleDocumentSelection(doc.doc_id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <FileText className="w-4 h-4 text-gray-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {doc.filename}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    {getStatusIcon(doc.status)}
                    <span>{getStatusText(doc.status)}</span>
                    {doc.status === 'completed' && (
                      <span>· {doc.total_chunks} 块</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(doc.doc_id)
                  }}
                  className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedDocIds.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-gray-600">
            已选择 {selectedDocIds.length} 个文档用于问答
          </p>
        </div>
      )}
    </div>
  )
}
