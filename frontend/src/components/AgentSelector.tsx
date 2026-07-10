import { useEffect, useMemo, useState } from 'react'
import { Bot, ChevronDown } from 'lucide-react'
import { skillsApi, type SkillItem } from '../services/api'
import { useStore } from '../store/useStore'

export default function AgentSelector() {
  const [isOpen, setIsOpen] = useState(false)
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { selectedAgentId, setSelectedAgentId } = useStore()

  useEffect(() => {
    let isMounted = true
    setIsLoading(true)
    skillsApi.list()
      .then((data) => {
        if (isMounted) setSkills(data.skills || [])
      })
      .catch((error) => {
        console.error('Failed to load agent profiles:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  const selectedSkill = useMemo(
    () => skills.find((skill) => skill.skill_id === selectedAgentId),
    [selectedAgentId, skills],
  )

  const selectedLabel = selectedSkill?.name || 'Default assistant'

  return (
    <div className="relative inline-flex">
      <button
        type="button"
        aria-label="Select agent"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((value) => !value)}
        className="inline-flex h-8 items-center gap-2 rounded-lg border border-[#d8d6d2] bg-white px-3 text-xs font-semibold text-slate-700 shadow-sm transition-colors hover:border-blue-200 hover:bg-blue-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
      >
        <Bot className="h-3.5 w-3.5 text-slate-500" />
        <span className="max-w-[9rem] truncate">{selectedLabel}</span>
        <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <div
          role="listbox"
          aria-label="Agent profiles"
          className="absolute bottom-full left-0 z-30 mb-2 w-72 rounded-lg border border-[#e2e1de] bg-white p-1 shadow-lg dark:border-gray-700 dark:bg-gray-900"
        >
          <button
            type="button"
            role="option"
            aria-selected={!selectedAgentId}
            onClick={() => {
              setSelectedAgentId(null)
              setIsOpen(false)
            }}
            className={`w-full rounded-md px-3 py-2 text-left text-xs transition-colors ${
              !selectedAgentId
                ? 'bg-blue-50 text-blue-700'
                : 'text-slate-700 hover:bg-[#f5f4f3] dark:text-gray-200 dark:hover:bg-gray-800'
            }`}
          >
            <span className="block font-semibold">Default assistant</span>
            <span className="mt-0.5 block text-[11px] text-slate-500">Chat with selected source context.</span>
          </button>

          {isLoading && (
            <div className="px-3 py-2 text-xs text-slate-500">Loading agent profiles</div>
          )}

          {skills.map((skill) => {
            const isActive = selectedAgentId === skill.skill_id
            return (
              <button
                key={skill.skill_id}
                type="button"
                role="option"
                aria-selected={isActive}
                onClick={() => {
                  setSelectedAgentId(skill.skill_id)
                  setIsOpen(false)
                }}
                className={`w-full rounded-md px-3 py-2 text-left text-xs transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-700 hover:bg-[#f5f4f3] dark:text-gray-200 dark:hover:bg-gray-800'
                }`}
              >
                <span className="block font-semibold">{skill.name}</span>
                <span className="mt-0.5 line-clamp-2 block text-[11px] text-slate-500">{skill.description}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
