import { useEffect, useState } from 'react'
import { Loader2, Play, RefreshCw, Wrench } from 'lucide-react'
import { agentsApi, skillsApi, type SkillItem } from '../services/api'
import { useStore } from '../store/useStore'

interface SkillsViewProps { onRunCreated: () => void }

export default function SkillsView({ onRunCreated }: SkillsViewProps) {
  const { selectedDocIds, addToast } = useStore()
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState<string | null>(null)

  const loadSkills = async () => {
    setLoading(true)
    try { setSkills((await skillsApi.list()).skills) }
    catch (error) { console.error(error); addToast('Failed to load skills', 'error') }
    finally { setLoading(false) }
  }

  useEffect(() => { void loadSkills() }, [])

  const startRun = async (skill: SkillItem) => {
    setRunning(skill.skill_id)
    try {
      await agentsApi.createRun({ skill_id: skill.skill_id, doc_ids: selectedDocIds, request: '' })
      addToast(`${skill.name} started`, 'success')
      onRunCreated()
    } catch (error) { console.error(error); addToast('Failed to start agent run', 'error') }
    finally { setRunning(null) }
  }

  return <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center justify-between"><div><h2 className="text-xl font-semibold text-gray-950 dark:text-gray-100">Skills</h2><p className="text-sm text-gray-500">Inspect local manifests and run them against selected sources.</p></div><button onClick={loadSkills} className="rounded-lg border border-gray-200 p-2 dark:border-gray-700" aria-label="Refresh skills"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button></div>
      <p className="mb-4 text-xs text-gray-500">{selectedDocIds.length} selected sources</p>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{skills.map((skill) => <article key={skill.skill_id} className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"><Wrench className="mb-3 h-5 w-5 text-blue-600" /><h3 className="font-semibold text-gray-950 dark:text-gray-100">{skill.name}</h3><p className="mt-2 min-h-10 text-sm text-gray-600 dark:text-gray-300">{skill.description}</p><p className="mt-3 text-xs text-gray-500">Output: {skill.output_kind}</p><p className="mt-1 text-xs text-gray-500">Tools: {skill.allowed_tools.join(', ')}</p><button onClick={() => startRun(skill)} disabled={running === skill.skill_id} className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">{running === skill.skill_id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}Run skill</button></article>)}</div>
      {!loading && skills.length === 0 && <p className="py-12 text-center text-sm text-gray-500">No local skill manifests found.</p>}
    </div>
  </div>
}
