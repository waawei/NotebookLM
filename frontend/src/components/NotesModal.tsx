import { useState, useEffect, useCallback, useRef } from 'react'
import { X, Save, FileText, Edit3, Trash2, Plus, Check, Quote } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useStore } from '../store/useStore'

const API_BASE_URL = 'http://localhost:8000'
const AUTO_SAVE_DELAY = 3000 // 3 seconds

interface Note {
  note_id: string
  title: string
  content: string
  doc_ids: string[]
  created_at: string
  updated_at: string
}

interface NotesModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function NotesModal({ isOpen, onClose }: NotesModalProps) {
  const [notes, setNotes] = useState<Note[]>([])
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [isPreview, setIsPreview] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [showCitationPicker, setShowCitationPicker] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { messages, documents } = useStore()

  useEffect(() => {
    if (isOpen) {
      fetchNotes()
    }
  }, [isOpen])

  // Auto-save effect
  useEffect(() => {
    if (!isEditing || !hasUnsavedChanges || !selectedNote) return

    const timer = setTimeout(() => {
      handleAutoSave()
    }, AUTO_SAVE_DELAY)

    return () => clearTimeout(timer)
  }, [editTitle, editContent, isEditing, hasUnsavedChanges, selectedNote])

  // Keyboard shortcut: Ctrl/Cmd + S to save
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's' && isEditing) {
        e.preventDefault()
        handleSaveNote()
      }
      // ESC to close citation picker
      if (e.key === 'Escape' && showCitationPicker) {
        setShowCitationPicker(false)
      }
    }

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
      return () => window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, isEditing, showCitationPicker])

  const fetchNotes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notes/list`)
      const data = await response.json()
      setNotes(data.notes)
    } catch (error) {
      console.error('Failed to fetch notes:', error)
    }
  }

  const handleCreateNote = () => {
    setSelectedNote(null)
    setIsEditing(true)
    setEditTitle('Untitled Note')
    setEditContent('# New Note\n\nStart writing here...')
    setIsPreview(false)
    setHasUnsavedChanges(false)
    setLastSaved(null)
  }

  const handleSelectNote = (note: Note) => {
    setSelectedNote(note)
    setIsEditing(false)
    setIsPreview(true)
  }

  const handleEditNote = () => {
    if (selectedNote) {
      setEditTitle(selectedNote.title)
      setEditContent(selectedNote.content)
      setIsEditing(true)
      setIsPreview(false)
      setHasUnsavedChanges(false)
    }
  }

  const handleAutoSave = async () => {
    if (!selectedNote) return

    setIsSaving(true)
    try {
      await fetch(`${API_BASE_URL}/api/notes/${selectedNote.note_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: editTitle,
          content: editContent,
        }),
      })

      setHasUnsavedChanges(false)
      setLastSaved(new Date())
    } catch (error) {
      console.error('Auto-save failed:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveNote = async () => {
    setIsSaving(true)
    try {
      if (selectedNote) {
        // Update existing note
        await fetch(`${API_BASE_URL}/api/notes/${selectedNote.note_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: editTitle,
            content: editContent,
          }),
        })
      } else {
        // Create new note
        const response = await fetch(`${API_BASE_URL}/api/notes/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: editTitle,
            content: editContent,
            doc_ids: [],
          }),
        })

        if (response.ok) {
          const data = await response.json()
          // Set the newly created note as selected
          const newNoteResponse = await fetch(`${API_BASE_URL}/api/notes/${data.note_id}`)
          const newNote = await newNoteResponse.json()
          setSelectedNote(newNote)
        }
      }

      await fetchNotes()
      setHasUnsavedChanges(false)
      setLastSaved(new Date())
      setIsEditing(false)
      setIsPreview(true)
    } catch (error) {
      console.error('Failed to save note:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteNote = async () => {
    if (!selectedNote) return

    if (confirm('Are you sure you want to delete this note?')) {
      try {
        await fetch(`${API_BASE_URL}/api/notes/${selectedNote.note_id}`, {
          method: 'DELETE',
        })

        await fetchNotes()
        setSelectedNote(null)
        setIsEditing(false)
      } catch (error) {
        console.error('Failed to delete note:', error)
      }
    }
  }

  const insertCitation = (type: 'message' | 'document', index: number) => {
    let citation = ''

    if (type === 'message') {
      const message = messages[index]
      if (message) {
        const preview = message.content.substring(0, 100).replace(/\n/g, ' ')
        citation = `\n> **Quote from conversation:**\n> ${preview}${message.content.length > 100 ? '...' : ''}\n\n`
      }
    } else if (type === 'document') {
      const doc = documents[index]
      if (doc) {
        citation = `\n> **Source:** ${doc.filename}\n> Document ID: ${doc.doc_id}\n\n`
      }
    }

    // 在光标位置插入引用
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart
      const end = textareaRef.current.selectionEnd
      const newContent = editContent.substring(0, start) + citation + editContent.substring(end)
      setEditContent(newContent)
      setHasUnsavedChanges(true)

      // 聚焦回文本框
      setTimeout(() => {
        textareaRef.current?.focus()
        const newPosition = start + citation.length
        textareaRef.current?.setSelectionRange(newPosition, newPosition)
      }, 0)
    }

    setShowCitationPicker(false)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-6xl h-[90vh] bg-white rounded-2xl shadow-2xl flex overflow-hidden">
        {/* Left Sidebar - Notes List */}
        <div className="w-80 border-r border-gray-200 flex flex-col bg-gray-50">
          <div className="p-4 border-b border-gray-200 bg-white">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Notes</h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <button
              onClick={handleCreateNote}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">New Note</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {notes.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No notes yet</p>
              </div>
            ) : (
              notes.map((note) => (
                <button
                  key={note.note_id}
                  onClick={() => handleSelectNote(note)}
                  className={`w-full text-left p-3 rounded-xl transition-all ${
                    selectedNote?.note_id === note.note_id
                      ? 'bg-blue-50 border-2 border-blue-400'
                      : 'bg-white border-2 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <p className="font-semibold text-sm text-gray-900 truncate mb-1">
                    {note.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(note.updated_at).toLocaleDateString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right - Note Content */}
        <div className="flex-1 flex flex-col">
          {selectedNote || isEditing ? (
            <>
              {/* Header */}
              <div className="p-4 border-b border-gray-200 bg-white flex items-center justify-between">
                <input
                  type="text"
                  value={isEditing ? editTitle : selectedNote?.title || ''}
                  onChange={(e) => {
                    setEditTitle(e.target.value)
                    setHasUnsavedChanges(true)
                  }}
                  disabled={!isEditing}
                  className="text-xl font-bold text-gray-900 bg-transparent border-none outline-none flex-1"
                />
                <div className="flex items-center gap-3">
                  {/* Save Status Indicator */}
                  {isEditing && (
                    <div className="flex items-center gap-2 text-xs">
                      {isSaving ? (
                        <span className="text-gray-500 flex items-center gap-1">
                          <span className="inline-block w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                          Saving...
                        </span>
                      ) : hasUnsavedChanges ? (
                        <span className="text-amber-600">Unsaved changes</span>
                      ) : lastSaved ? (
                        <span className="text-green-600 flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          Saved {lastSaved.toLocaleTimeString()}
                        </span>
                      ) : null}
                    </div>
                  )}

                  {isEditing ? (
                    <>
                      <button
                        onClick={() => setIsPreview(!isPreview)}
                        className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        {isPreview ? 'Edit' : 'Preview'}
                      </button>
                      <button
                        onClick={handleSaveNote}
                        disabled={isSaving}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Save className="w-4 h-4" />
                        <span className="text-sm font-medium">Save</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={handleEditNote}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        <Edit3 className="w-4 h-4 text-gray-600" />
                      </button>
                      <button
                        onClick={handleDeleteNote}
                        className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {isEditing && !isPreview ? (
                  <div className="relative h-full">
                    <textarea
                      ref={textareaRef}
                      value={editContent}
                      onChange={(e) => {
                        setEditContent(e.target.value)
                        setHasUnsavedChanges(true)
                      }}
                      className="w-full h-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-400 outline-none resize-none font-mono text-sm"
                      placeholder="Write your note in Markdown..."
                    />

                    {/* Insert Citation Button */}
                    <div className="absolute bottom-4 right-4">
                      <button
                        onClick={() => setShowCitationPicker(!showCitationPicker)}
                        className="flex items-center gap-2 px-3 py-2 bg-white border-2 border-gray-300 hover:border-blue-400 rounded-lg shadow-md hover:shadow-lg transition-all"
                        title="Insert citation"
                      >
                        <Quote className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">Insert Citation</span>
                      </button>

                      {/* Citation Picker Dropdown */}
                      {showCitationPicker && (
                        <div className="absolute bottom-full right-0 mb-2 w-80 max-h-96 overflow-y-auto bg-white border-2 border-gray-300 rounded-xl shadow-2xl">
                          {/* Documents Section */}
                          {documents.length > 0 && (
                            <div className="border-b border-gray-200">
                              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                                <p className="text-xs font-bold text-gray-700 uppercase tracking-wider">Documents</p>
                              </div>
                              <div className="p-2">
                                {documents.map((doc, idx) => (
                                  <button
                                    key={doc.doc_id}
                                    onClick={() => insertCitation('document', idx)}
                                    className="w-full text-left px-3 py-2 hover:bg-blue-50 rounded-lg transition-colors"
                                  >
                                    <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                                    <p className="text-xs text-gray-500 truncate">{doc.doc_id}</p>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Messages Section */}
                          {messages.length > 0 && (
                            <div>
                              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                                <p className="text-xs font-bold text-gray-700 uppercase tracking-wider">Conversation</p>
                              </div>
                              <div className="p-2">
                                {messages.map((message, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => insertCitation('message', idx)}
                                    className="w-full text-left px-3 py-2 hover:bg-blue-50 rounded-lg transition-colors"
                                  >
                                    <p className="text-xs font-semibold text-gray-600 mb-1">
                                      {message.role === 'user' ? 'You' : 'Assistant'}
                                    </p>
                                    <p className="text-sm text-gray-800 line-clamp-2">
                                      {message.content}
                                    </p>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {documents.length === 0 && messages.length === 0 && (
                            <div className="px-4 py-8 text-center">
                              <p className="text-sm text-gray-500">No citations available</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{isEditing ? editContent : selectedNote?.content || ''}</ReactMarkdown>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 font-medium">Select a note or create a new one</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
