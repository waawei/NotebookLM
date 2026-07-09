import {
  BookOpen,
  BookOpenText,
  FileStack,
  Home,
  Settings,
  Sparkles,
  StickyNote,
} from 'lucide-react'
import type { AppModule } from '../store/useStore'

interface ModuleNavProps {
  activeModule: AppModule
  onModuleChange: (module: AppModule) => void
}

const modules: Array<{
  key: AppModule
  label: string
  icon: typeof Home
}> = [
  { key: 'dashboard', label: 'Dashboard', icon: Home },
  { key: 'workbench', label: 'Workbench', icon: BookOpen },
  { key: 'sources', label: 'Sources', icon: FileStack },
  { key: 'notes', label: 'Notes', icon: StickyNote },
  { key: 'wiki', label: 'Wiki', icon: BookOpenText },
  { key: 'outputs', label: 'Outputs', icon: Sparkles },
  { key: 'settings', label: 'Settings', icon: Settings },
]

export default function ModuleNav({ activeModule, onModuleChange }: ModuleNavProps) {
  return (
    <nav className="h-full w-16 flex-shrink-0 border-r border-gray-200 dark:border-gray-800 bg-gray-950 text-gray-300">
      <div className="flex h-16 items-center justify-center border-b border-gray-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm">
          <BookOpen className="h-5 w-5" />
        </div>
      </div>

      <div className="flex flex-col items-center gap-1 px-2 py-3">
        {modules.map((item) => {
          const Icon = item.icon
          const isActive = activeModule === item.key

          return (
            <button
              key={item.key}
              onClick={() => onModuleChange(item.key)}
              className={`group relative flex h-11 w-11 items-center justify-center rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
              title={item.label}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="h-5 w-5" />
              <span className="pointer-events-none absolute left-12 z-30 hidden whitespace-nowrap rounded-md bg-gray-900 px-2 py-1 text-xs font-medium text-white shadow-lg group-hover:block">
                {item.label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
