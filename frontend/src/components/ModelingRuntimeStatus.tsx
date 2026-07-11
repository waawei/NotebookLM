import { AlertCircle, CheckCircle2, FolderCheck, GitBranch, Terminal, Type } from 'lucide-react'
import { type ModelingRuntimeStatus as RuntimeStatus } from '../services/api'

export default function ModelingRuntimeStatus({ status }: { status: RuntimeStatus }) {
  const capabilities = [
    { label: 'Workspace', available: status.workspace.configured && status.workspace.writable, version: null, icon: FolderCheck },
    { label: 'Python', available: status.python.available, version: status.python.version, icon: Terminal },
    { label: 'Git', available: status.git.available, version: status.git.version, icon: GitBranch },
    { label: 'XeLaTeX', available: status.xelatex.available, version: status.xelatex.version, icon: Type },
  ]

  return (
    <section aria-label="Runtime readiness" className="border border-gray-200 p-3 dark:border-gray-800">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Runtime readiness</h2>
      <ul className="mt-3 grid gap-2 sm:grid-cols-2">
        {capabilities.map(({ label, available, version, icon: Icon }) => (
          <li key={label} className="flex min-w-0 items-center gap-2 text-sm">
            <Icon className="h-4 w-4 shrink-0 text-gray-500" aria-hidden="true" />
            <span className="font-medium text-gray-800 dark:text-gray-200">{label}</span>
            {available
              ? <CheckCircle2 className="h-4 w-4 shrink-0 text-green-700" aria-label={`${label} ready`} />
              : <AlertCircle className="h-4 w-4 shrink-0 text-amber-700" aria-label={`${label} unavailable`} />}
            <span className={available ? 'text-green-700 dark:text-green-400' : 'text-amber-700 dark:text-amber-400'}>{available ? 'Ready' : 'Unavailable'}</span>
            {version && <span className="min-w-0 truncate text-xs text-gray-500 dark:text-gray-400" title={version}>{version}</span>}
          </li>
        ))}
      </ul>
    </section>
  )
}
