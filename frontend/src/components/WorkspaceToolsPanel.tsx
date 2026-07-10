import { useEffect, useState } from 'react'
import { Brain, FileText, Layers, ListChecks, Network, Sparkles } from 'lucide-react'
import { skillsApi, type SkillItem } from '../services/api'
import { useStore } from '../store/useStore'

const tools = [
  { label: 'Mind map', description: 'Map concepts from selected sources.', icon: Network },
  { label: 'Quiz', description: 'Create retrieval-backed checks.', icon: ListChecks },
  { label: 'Flashcards', description: 'Extract compact study prompts.', icon: Layers },
  { label: 'Research brief', description: 'Draft a cited synthesis.', icon: FileText },
  { label: 'Paper outline', description: 'Plan sections and arguments.', icon: Brain },
]

export default function WorkspaceToolsPanel() {
  const [skills, setSkills] = useState<SkillItem[]>([])
  const { setPendingSkillCommand } = useStore()

  useEffect(() => {
    let isMounted = true
    skillsApi.list()
      .then((data) => {
        if (isMounted) setSkills(data.skills || [])
      })
      .catch((error) => {
        console.error('Failed to load workspace skills:', error)
      })

    return () => {
      isMounted = false
    }
  }, [])

  const prepareSkillCommand = (skill: SkillItem) => {
    setPendingSkillCommand({ skill_id: skill.skill_id, text: `/${skill.skill_id} ` })
  }

  return (
    <div className="space-y-4">
      <section aria-labelledby="workspace-tools-heading">
        <h3 id="workspace-tools-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Tools
        </h3>
        <div className="mt-2 grid grid-cols-1 gap-2">
          {tools.map((tool) => {
            const Icon = tool.icon
            return (
              <article
                key={tool.label}
                className="rounded-lg border border-[#e2e1de] bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-gray-900"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-[#f5f4f3] text-slate-600 dark:bg-gray-800 dark:text-gray-300">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">{tool.label}</p>
                    <p className="mt-0.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{tool.description}</p>
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      </section>

      <section aria-labelledby="workspace-skills-heading">
        <h3 id="workspace-skills-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Skills
        </h3>
        <div className="mt-2 space-y-2">
          {skills.length === 0 ? (
            <div className="rounded-lg border border-[#e2e1de] bg-white p-3 text-xs text-slate-500 dark:border-gray-800 dark:bg-gray-900">
              No skills registered
            </div>
          ) : (
            skills.map((skill) => (
              <button
                key={skill.skill_id}
                type="button"
                data-testid={`workspace-skill-card-${skill.skill_id}`}
                onClick={() => prepareSkillCommand(skill)}
                className="w-full rounded-lg border border-[#e2e1de] bg-white p-3 text-left shadow-sm transition-colors hover:border-blue-200 hover:bg-blue-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-900 dark:hover:bg-blue-950"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-semibold text-slate-950 dark:text-slate-100">{skill.name}</p>
                      <span className="rounded-md border border-[#e2e1de] bg-[#f5f4f3] px-2 py-0.5 text-[11px] font-semibold text-slate-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
                        {skill.output_kind}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                      {skill.description}
                    </p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
