import {
  BookOpen,
  BookOpenText,
  Bot,
  FileStack,
  Home,
  Settings,
  Sparkles,
  StickyNote,
  Wrench,
} from 'lucide-react'
import { t } from '../i18n'
import { useStore, type AppModule } from '../store/useStore'

interface ModuleNavProps {
  activeModule: AppModule
  onModuleChange: (module: AppModule) => void
}

const modules: Array<{
  key: AppModule
  labelKey:
    | 'nav.dashboard'
    | 'nav.workbench'
    | 'nav.sources'
    | 'nav.notes'
    | 'nav.wiki'
    | 'nav.outputs'
    | 'nav.skills'
    | 'nav.agents'
    | 'nav.settings'
  icon: typeof Home
}> = [
  { key: 'dashboard', labelKey: 'nav.dashboard', icon: Home },
  { key: 'workbench', labelKey: 'nav.workbench', icon: BookOpen },
  { key: 'sources', labelKey: 'nav.sources', icon: FileStack },
  { key: 'notes', labelKey: 'nav.notes', icon: StickyNote },
  { key: 'wiki', labelKey: 'nav.wiki', icon: BookOpenText },
  { key: 'outputs', labelKey: 'nav.outputs', icon: Sparkles },
  { key: 'skills', labelKey: 'nav.skills', icon: Wrench },
  { key: 'agents', labelKey: 'nav.agents', icon: Bot },
  { key: 'settings', labelKey: 'nav.settings', icon: Settings },
]

export default function ModuleNav({ activeModule, onModuleChange }: ModuleNavProps) {
  const language = useStore((state) => state.language)

  return (
    <nav className="h-full w-16 flex-shrink-0 border-r-2 border-[#dddcd9] bg-[#f1f0ef] text-[#8a8a9e] transition-colors dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">
      <div className="flex h-16 items-center justify-center border-b border-[#dddcd9] dark:border-gray-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600 shadow-sm ring-1 ring-blue-100">
          <BookOpen className="h-5 w-5" />
        </div>
      </div>

      <div className="flex flex-col items-center gap-1 px-2 py-3">
        {modules.map((item) => {
          const Icon = item.icon
          const isActive = activeModule === item.key
          const label = t(language, item.labelKey)

          return (
            <button
              key={item.key}
              onClick={() => onModuleChange(item.key)}
              className={`group relative flex h-11 w-11 items-center justify-center rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 text-[#1a1a2e] ring-1 ring-blue-100 dark:bg-blue-950 dark:text-blue-100 dark:ring-blue-900'
                  : 'text-[#8a8a9e] hover:bg-[#ebeae8] hover:text-[#1a1a2e] dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white'
              }`}
              title={label}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
            >
              {isActive && (
                <span
                  data-testid="active-rail-indicator"
                  className="absolute -left-2 top-2 bottom-2 w-0.5 rounded-r bg-blue-500"
                />
              )}
              <Icon className="h-5 w-5" />
              <span className="pointer-events-none absolute left-12 z-30 hidden whitespace-nowrap rounded-md bg-gray-900 px-2 py-1 text-xs font-medium text-white shadow-lg group-hover:block dark:bg-gray-800">
                {label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
