import { useEffect, useState } from 'react'
import { Edit3, FileText, Loader2, Plus, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { noteApi, type NoteItem } from '../services/api'
import { useStore } from '../store/useStore'

interface NotesViewProps {
  onOpenNotesModal: () => void
}

export default function NotesView({ onOpenNotesModal }: NotesViewProps) {
  const [notes, setNotes] = useState<NoteItem[]>([])
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { addToast } = useStore()

  useEffect(() => {
    loadNotes()
  }, [])

  const selectedNote = notes.find((note) => note.note_id === selectedNoteId) || notes[0] || null

  const loadNotes = async () => {
    setIsLoading(true)
    try {
      const data = await noteApi.list()
      setNotes(data.notes)
      setSelectedNoteId((current) => current || data.notes[0]?.note_id || null)
    } catch (error) {
      console.error('Failed to load notes:', error)
      addToast('Failed to load notes', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="grid h-full grid-cols-[minmax(260px,320px)_1fr] bg-gray-100 dark:bg-gray-950">
      <aside className="min-h-0 border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="border-b border-gray-200 p-4 dark:border-gray-800">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Notes</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">{notes.length} saved items</p>
            </div>
            <button
              onClick={loadNotes}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
              title="Refresh notes"
              aria-label="Refresh notes"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <button
            onClick={onOpenNotesModal}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            New or edit note
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          {isLoading && notes.length === 0 ? (
            <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading notes
            </div>
          ) : notes.length === 0 ? (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-700" />
              <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">No notes yet</p>
              <p className="mt-1 px-4 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
                Save answers or create notes to build reusable knowledge.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {notes.map((note) => {
                const isSelected = selectedNote?.note_id === note.note_id

                return (
                  <button
                    key={note.note_id}
                    onClick={() => setSelectedNoteId(note.note_id)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      isSelected
                        ? 'border-blue-400 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
                        : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:bg-gray-800'
                    }`}
                  >
                    <p className="truncate text-sm font-medium text-gray-950 dark:text-gray-100">{note.title}</p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {new Date(note.updated_at).toLocaleString()}
                    </p>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </aside>

      <main className="min-w-0 overflow-y-auto p-6">
        {selectedNote ? (
          <article className="mx-auto max-w-3xl rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-5 flex items-start justify-between gap-3 border-b border-gray-100 pb-4 dark:border-gray-800">
              <div className="min-w-0">
                <h1 className="truncate text-xl font-semibold text-gray-950 dark:text-gray-100">{selectedNote.title}</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Updated {new Date(selectedNote.updated_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={onOpenNotesModal}
                className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                <Edit3 className="h-4 w-4" />
                Edit
              </button>
            </div>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{selectedNote.content}</ReactMarkdown>
            </div>
          </article>
        ) : (
          <div className="flex h-full items-center justify-center text-center">
            <div>
              <FileText className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-700" />
              <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">Select or create a note</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
