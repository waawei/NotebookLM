import { useEffect, useMemo, useState } from 'react'
import { X } from 'lucide-react'
import { wikiApi, type WikiPage } from '../services/api'
import { t } from '../i18n'
import { useStore } from '../store/useStore'

export default function ContextPillBar() {
  const [wikiPages, setWikiPages] = useState<WikiPage[]>([])
  const {
    documents,
    selectedDocIds,
    selectedWikiPageIds,
    toggleDocumentSelection,
    toggleWikiContext,
    language,
  } = useStore()

  useEffect(() => {
    let isMounted = true
    wikiApi.list()
      .then((data) => {
        if (isMounted) setWikiPages(data.pages || [])
      })
      .catch((error) => {
        console.error('Failed to load wiki context pills:', error)
      })
    return () => {
      isMounted = false
    }
  }, [])

  const selectedDocuments = useMemo(
    () => documents.filter((document) => selectedDocIds.includes(document.doc_id)),
    [documents, selectedDocIds],
  )

  const selectedWikiPages = useMemo(
    () => wikiPages.filter((page) => selectedWikiPageIds.includes(page.page_id)),
    [wikiPages, selectedWikiPageIds],
  )

  if (selectedDocuments.length === 0 && selectedWikiPages.length === 0) {
    return (
      <div className="mb-3 text-xs font-medium text-slate-500 dark:text-slate-400">
        {t(language, 'chat.noContext')}
      </div>
    )
  }

  return (
    <div className="mb-3 flex max-h-20 flex-wrap gap-2 overflow-y-auto">
      {selectedDocuments.map((document) => (
        <span
          key={document.doc_id}
          className="inline-flex min-w-0 max-w-full items-center gap-1.5 rounded-md border border-[#e2e1de] bg-white px-2.5 py-1 text-xs font-medium text-slate-700 shadow-sm dark:border-gray-800 dark:bg-gray-900 dark:text-slate-200"
        >
          <span className="truncate">{document.filename}</span>
          <button
            type="button"
            aria-label={`Remove source ${document.filename}`}
            onClick={() => toggleDocumentSelection(document.doc_id)}
            className="rounded p-0.5 text-slate-400 hover:bg-[#ebeae8] hover:text-slate-700 dark:hover:bg-gray-800 dark:hover:text-slate-200"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      {selectedWikiPages.map((page) => (
        <span
          key={page.page_id}
          className="inline-flex min-w-0 max-w-full items-center gap-1.5 rounded-md border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 shadow-sm dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200"
        >
          <span className="truncate">{page.title}</span>
          <button
            type="button"
            aria-label={`Remove wiki ${page.title}`}
            onClick={() => toggleWikiContext(page.page_id)}
            className="rounded p-0.5 text-blue-400 hover:bg-blue-100 hover:text-blue-700 dark:hover:bg-blue-900"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
    </div>
  )
}
