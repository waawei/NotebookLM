import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Loader2, Lightbulb, ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
import { useStore } from '../store/useStore'
import ReactMarkdown from 'react-markdown'

const API_BASE_URL = 'http://localhost:8000'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const [expandedCitations, setExpandedCitations] = useState<Set<string>>(new Set())
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    messages,
    selectedDocIds,
    conversationId,
    isLoading,
    suggestedQuestions,
    addMessage,
    updateMessageAtIndex,
    setConversationId,
    setLoading,
    setSuggestedQuestions,
    addToast
  } = useStore()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  // 当文档选择改变时，获取建议问题
  useEffect(() => {
    if (selectedDocIds.length > 0 && messages.length === 0) {
      fetchSuggestedQuestions()
    }
  }, [selectedDocIds])

  const fetchSuggestedQuestions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/suggest-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedDocIds),
      })
      const data = await response.json()
      setSuggestedQuestions(data.questions || [])
    } catch (error) {
      console.error('Failed to fetch suggested questions:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    if (selectedDocIds.length === 0) {
      alert('Please select at least one document')
      return
    }

    const userMessage = { role: 'user' as const, content: input }
    addMessage(userMessage)
    setInput('')
    setLoading(true)

    try {
      // 使用流式 API
      const response = await fetch(`${API_BASE_URL}/api/chat/ask-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          doc_ids: selectedDocIds,
          conversation_id: conversationId,
        }),
      })

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let accumulatedAnswer = ''
      let citations: any[] = []
      let streamConversationId = conversationId

      // 创建临时的助手消息
      const tempMessageIndex = messages.length + 1
      addMessage({
        role: 'assistant',
        content: '',
        citations: [],
      })

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'start') {
                streamConversationId = data.conversation_id
                if (!conversationId) {
                  setConversationId(streamConversationId)
                }
              } else if (data.type === 'content') {
                // 累积回答内容
                accumulatedAnswer += data.content
                // 实时更新消息
                updateMessageAtIndex(tempMessageIndex, {
                  role: 'assistant',
                  content: accumulatedAnswer,
                  citations: citations,
                })
              } else if (data.type === 'citations') {
                citations = data.citations
                // 更新引用
                updateMessageAtIndex(tempMessageIndex, {
                  role: 'assistant',
                  content: accumulatedAnswer,
                  citations: citations,
                })
              } else if (data.type === 'error') {
                throw new Error(data.message)
              }
            } catch (parseError) {
              console.error('Failed to parse SSE data:', parseError)
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      addMessage({
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  const toggleCitationExpand = (messageIndex: number, citationIndex: number) => {
    const key = `${messageIndex}-${citationIndex}`
    setExpandedCitations((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
  }

  const isCitationExpanded = (messageIndex: number, citationIndex: number) => {
    return expandedCitations.has(`${messageIndex}-${citationIndex}`)
  }

  const handleSaveAsNote = async (messageIndex: number) => {
    const message = messages[messageIndex]
    if (!message || message.role !== 'assistant') return

    try {
      // 创建笔记内容
      const title = `Note from Conversation - ${new Date().toLocaleDateString()}`
      let content = `# ${title}\n\n`
      content += `## Question\n${messages[messageIndex - 1]?.content || ''}\n\n`
      content += `## Answer\n${message.content}\n\n`

      if (message.citations && message.citations.length > 0) {
        content += `## Sources\n`
        message.citations.forEach(citation => {
          content += `- [${citation.number}] ${citation.doc_name} (${Math.round(citation.relevance_score * 100)}%)\n`
        })
      }

      const response = await fetch(`${API_BASE_URL}/api/notes/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          content,
          doc_ids: selectedDocIds,
          conversation_id: conversationId
        }),
      })

      if (response.ok) {
        addToast('Saved to notes successfully!', 'success')
      } else {
        throw new Error('Failed to save note')
      }
    } catch (error) {
      console.error('Failed to save note:', error)
      addToast('Failed to save note', 'error')
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-br from-white to-blue-50 dark:from-gray-900 dark:to-gray-800">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center p-8">
            <div className="text-center max-w-2xl">
              <div className="relative mb-6">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-700 rounded-3xl flex items-center justify-center mx-auto shadow-xl">
                  <Sparkles className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                Ready to explore your sources
              </h2>
              <p className="text-base text-gray-600 dark:text-gray-400 leading-relaxed mb-8">
                Upload documents and ask questions. I'll provide answers with citations from your sources.
              </p>

              {/* 建议问题 */}
              {suggestedQuestions.length > 0 && (
                <div className="mt-8">
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <Lightbulb className="w-5 h-5 text-amber-500" />
                    <p className="text-sm font-semibold text-gray-700">Suggested questions</p>
                  </div>
                  <div className="grid gap-3 text-left">
                    {suggestedQuestions.map((question, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInput(question)}
                        className="p-4 bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all text-left group shadow-sm hover:shadow-md"
                      >
                        <p className="text-sm text-gray-800 group-hover:text-blue-900 font-medium">
                          {question}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white rounded-3xl rounded-br-md shadow-lg'
                      : 'bg-white dark:bg-gray-800 rounded-3xl rounded-bl-md shadow-lg border border-gray-100 dark:border-gray-700'
                  } px-6 py-4`}
                >
                  <div className={`prose prose-sm max-w-none ${
                    message.role === 'user' ? 'prose-invert' : 'prose-gray'
                  }`}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>

                  {/* Save as Note Button (for assistant messages) */}
                  {message.role === 'assistant' && message.content && (
                    <div className="mt-3 flex justify-end">
                      <button
                        onClick={() => handleSaveAsNote(index)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        Save as Note
                      </button>
                    </div>
                  )}

                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200 space-y-2">
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Sources</p>
                      <div className="space-y-2">
                        {message.citations.map((citation, citIndex) => {
                          const isExpanded = isCitationExpanded(index, citIndex)
                          return (
                            <div
                              key={citIndex}
                              className="bg-blue-50 rounded-xl border-2 border-blue-200 hover:border-blue-400 transition-all hover:shadow-md overflow-hidden"
                            >
                              <button
                                onClick={() => toggleCitationExpand(index, citIndex)}
                                className="w-full p-3 text-left"
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex items-center gap-2 flex-1">
                                    <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full flex-shrink-0">
                                      {citation.number}
                                    </span>
                                    <p className="text-xs font-bold text-blue-900">
                                      {citation.doc_name}
                                      {citation.page && <span className="ml-2 text-blue-700">· Page {citation.page}</span>}
                                    </p>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-blue-700 bg-blue-200 px-2 py-1 rounded-full">
                                      {Math.round(citation.relevance_score * 100)}%
                                    </span>
                                    {isExpanded ? (
                                      <ChevronUp className="w-4 h-4 text-blue-600" />
                                    ) : (
                                      <ChevronDown className="w-4 h-4 text-blue-600" />
                                    )}
                                  </div>
                                </div>
                                <p className={`text-xs text-gray-800 leading-relaxed ${isExpanded ? '' : 'line-clamp-2'}`}>
                                  {citation.content}
                                </p>
                              </button>

                              {/* 展开的完整内容 */}
                              {isExpanded && (
                                <div className="px-3 pb-3 pt-0 border-t border-blue-200 bg-blue-25">
                                  <div className="mt-2 p-3 bg-white rounded-lg border border-blue-100">
                                    <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">
                                      {citation.content}
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white rounded-3xl rounded-bl-md shadow-lg border border-gray-100 px-6 py-4 flex items-center space-x-3">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  <span className="text-sm text-gray-700 font-medium">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl border-2 border-gray-300 dark:border-gray-600 focus-within:border-blue-500 dark:focus-within:border-blue-400 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
              placeholder="Ask a question about your sources..."
              className="w-full px-5 py-4 pr-14 bg-transparent border-none outline-none resize-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 text-sm leading-relaxed min-h-[56px] max-h-[200px]"
              rows={1}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-3 bottom-3 p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
              aria-label="Send message"
            >
              <Send className="w-5 h-5" strokeWidth={2.5} />
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-3">
            Press <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-xs font-mono">Enter</kbd> to send, <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-xs font-mono">Shift + Enter</kbd> for new line
          </p>
        </form>
      </div>
    </div>
  )
}
