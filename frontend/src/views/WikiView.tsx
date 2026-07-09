import { useEffect, useMemo, useState } from 'react'
import {
  BookOpenText,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Sparkles,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { wikiApi, type WikiPage } from '../services/api'
import type { AppModule } from '../store/useStore'
import { useStore } from '../store/useStore'

interface WikiViewProps {
  onModuleChange: (module: AppModule) => void
}

export default function WikiView({ onModuleChange }: WikiViewProps) {
  const { selectedDocIds, addToast } = useStore()
  const [pages, setPages] = useState<WikiPage[]>([])
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)
  const [draftTitle, setDraftTitle] = useState('')
  const [draftContent, setDraftContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  const selectedPage = useMemo(
    () => pages.find((page) => page.page_id === selectedPageId) || null,
    [pages, selectedPageId],
  )

  const provenanceDocIds = selectedPage?.source_doc_ids || selectedDocIds

  useEffect(() => {
    void loadPages()
  }, [])

  useEffect(() => {
    if (selectedPage) {
      setDraftTitle(selectedPage.title)
      setDraftContent(selectedPage.content)
      return
    }

    if (selectedPageId === null) {
      setDraftTitle('')
      setDraftContent('')
    }
  }, [selectedPage, selectedPageId])

  const loadPages = async () => {
    setIsLoading(true)
    try {
      const data = await wikiApi.list()
      setPages(data.pages)
      setSelectedPageId((current) => {
        if (current && data.pages.some((page) => page.page_id === current)) {
          return current
        }
        return data.pages[0]?.page_id || null
      })
    } catch (error) {
      console.error('Failed to load Wiki pages:', error)
      addToast('Failed to load Wiki pages', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewPage = () => {
    setSelectedPageId(null)
    setDraftTitle('')
    setDraftContent('')
  }

  const handleSave = async () => {
    const title = draftTitle.trim()
    if (!title) {
      addToast('Add a Wiki page title', 'error')
      return
    }

    setIsSaving(true)
    try {
      if (selectedPage) {
        await wikiApi.update(selectedPage.page_id, {
          title,
          content: draftContent,
        })
        setPages((current) =>
          current.map((page) =>
            page.page_id === selectedPage.page_id
              ? {
                  ...page,
                  title,
                  content: draftContent,
                  updated_at: new Date().toISOString(),
                }
              : page,
          ),
        )
        addToast('Wiki page updated', 'success')
        return
      }

      const created = await wikiApi.create({
        title,
        content: draftContent,
        source_doc_ids: selectedDocIds,
      })
      setPages((current) => [created, ...current])
      setSelectedPageId(created.page_id)
      addToast('Wiki page created', 'success')
    } catch (error) {
      console.error('Failed to save Wiki page:', error)
      addToast('Failed to save Wiki page', 'error')
    } finally {
      setIsSaving(false)
    }
  }

  const handleGenerate = async () => {
    const title = draftTitle.trim()
    if (!title) {
      addToast('Add a Wiki page title', 'error')
      return
    }
    if (selectedDocIds.length === 0) {
      addToast('Select at least one source first', 'error')
      return
    }

    setIsGenerating(true)
    try {
      const generated = await wikiApi.generate({
        title,
        source_doc_ids: selectedDocIds,
      })
      setPages((current) => [generated, ...current])
      setSelectedPageId(generated.page_id)
      addToast('Wiki page generated', 'success')
    } catch (error) {
      console.error('Failed to generate Wiki page:', error)
      addToast('Failed to generate Wiki page', 'error')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="grid h-full grid-cols-[minmax(280px,360px)_1fr] bg-gray-100 dark:bg-gray-950">
      <aside className="min-h-0 border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="border-b border-gray-200 p-4 dark:border-gray-800">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Wiki</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">{pages.length} pages</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleNewPage}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                title="New page"
                aria-label="New page"
              >
                <Plus className="h-4 w-4" />
              </button>
              <button
                onClick={loadPages}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                title="Refresh pages"
                aria-label="Refresh pages"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            {selectedDocIds.length} selected sources
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          {isLoading && pages.length === 0 ? (
            <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading pages
            </div>
          ) : pages.length === 0 ? (
            <div className="py-16 text-center">
              <BookOpenText className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-700" />
              <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">No Wiki pages yet</p>
              <button
                onClick={() => onModuleChange('sources')}
                className="mt-3 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                Select sources
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {pages.map((page) => {
                const isSelected = selectedPage?.page_id === page.page_id
                return (
                  <button
                    key={page.page_id}
                    onClick={() => setSelectedPageId(page.page_id)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      isSelected
                        ? 'border-blue-400 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
                        : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:bg-gray-800'
                    }`}
                  >
                    <p className="truncate text-sm font-medium text-gray-950 dark:text-gray-100">{page.title}</p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {page.source_doc_ids.length} sources - Updated {new Date(page.updated_at).toLocaleDateString()}
                    </p>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </aside>

      <main className="grid min-w-0 grid-cols-[minmax(320px,420px)_1fr] gap-4 overflow-y-auto p-6">
        <section className="min-w-0 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                {selectedPage ? 'Edit page' : 'New page'}
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {selectedPage ? selectedPage.page_id : 'Unsaved draft'}
              </p>
            </div>
            <FileText className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">Title</span>
              <input
                value={draftTitle}
                onChange={(event) => setDraftTitle(event.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">Markdown</span>
              <textarea
                value={draftContent}
                onChange={(event) => setDraftContent(event.target.value)}
                rows={16}
                className="w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 font-mono text-xs leading-5 text-gray-900 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
              />
            </label>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700"
              >
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save
              </button>
              <button
                onClick={handleGenerate}
                disabled={isGenerating || selectedDocIds.length === 0}
                className="flex items-center justify-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-400 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800 dark:disabled:text-gray-600"
              >
                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Generate
              </button>
            </div>
          </div>
        </section>

        <article className="min-w-0 rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-5 border-b border-gray-100 pb-4 dark:border-gray-800">
            <h1 className="truncate text-xl font-semibold text-gray-950 dark:text-gray-100">
              {draftTitle || 'Untitled Wiki Page'}
            </h1>
            <div className="mt-3 flex flex-wrap gap-2">
              {provenanceDocIds.length > 0 ? (
                provenanceDocIds.map((docId) => (
                  <span
                    key={docId}
                    className="max-w-full truncate rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-300"
                  >
                    {docId}
                  </span>
                ))
              ) : (
                <span className="text-xs text-gray-500 dark:text-gray-400">No source documents linked</span>
              )}
            </div>
          </div>

          {draftContent ? (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{draftContent}</ReactMarkdown>
            </div>
          ) : (
            <div className="flex min-h-64 items-center justify-center text-center">
              <div>
                <BookOpenText className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-700" />
                <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">No page content</p>
              </div>
            </div>
          )}
        </article>
      </main>
    </div>
  )
}
