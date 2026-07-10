import { useEffect, useMemo, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { skillsApi, type SkillItem } from '../services/api'

interface SlashCommandMenuProps {
  query: string
  onSelect: (skill: SkillItem) => void
  onClose: () => void
}

function normalizeQuery(query: string) {
  return query.replace(/^\//, '').trim().toLowerCase()
}

export default function SlashCommandMenu({ query, onSelect, onClose }: SlashCommandMenuProps) {
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [highlightedIndex, setHighlightedIndex] = useState(0)

  useEffect(() => {
    let isMounted = true
    skillsApi.list()
      .then((data) => {
        if (isMounted) setSkills(data.skills || [])
      })
      .catch((error) => {
        console.error('Failed to load skill commands:', error)
      })

    return () => {
      isMounted = false
    }
  }, [])

  const filteredSkills = useMemo(() => {
    const term = normalizeQuery(query)
    if (!term) return skills
    return skills.filter((skill) => {
      const haystack = `${skill.skill_id} ${skill.name} ${skill.description}`.toLowerCase()
      return haystack.includes(term)
    })
  }, [query, skills])

  useEffect(() => {
    setHighlightedIndex(0)
  }, [query])

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlightedIndex((index) => Math.min(index + 1, Math.max(filteredSkills.length - 1, 0)))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlightedIndex((index) => Math.max(index - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      const skill = filteredSkills[highlightedIndex]
      if (skill) onSelect(skill)
    } else if (event.key === 'Escape') {
      event.preventDefault()
      onClose()
    }
  }

  return (
    <div
      role="listbox"
      aria-label="Skill commands"
      tabIndex={-1}
      onKeyDown={handleKeyDown}
      className="absolute bottom-full left-3 right-3 z-20 mb-2 max-h-72 overflow-y-auto rounded-lg border border-[#e2e1de] bg-white p-1 shadow-lg outline-none dark:border-gray-700 dark:bg-gray-900"
    >
      {filteredSkills.length === 0 ? (
        <div className="px-3 py-3 text-xs text-slate-500">No matching skills</div>
      ) : (
        filteredSkills.map((skill, index) => {
          const isHighlighted = index === highlightedIndex
          return (
            <button
              key={skill.skill_id}
              type="button"
              role="option"
              aria-selected={isHighlighted}
              onMouseEnter={() => setHighlightedIndex(index)}
              onClick={() => onSelect(skill)}
              className={`flex w-full items-start gap-3 rounded-md px-3 py-2 text-left transition-colors ${
                isHighlighted
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-700 hover:bg-[#f5f4f3] dark:text-gray-200 dark:hover:bg-gray-800'
              }`}
            >
              <Sparkles className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
              <span className="min-w-0">
                <span className="block text-xs font-semibold">/{skill.skill_id}</span>
                <span className="mt-0.5 block truncate text-[11px] text-slate-500">
                  {skill.name} · {skill.output_kind}
                </span>
              </span>
            </button>
          )
        })
      )}
    </div>
  )
}
