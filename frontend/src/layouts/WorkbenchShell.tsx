import type { ReactNode } from 'react'
import {
  Download,
  FileText,
  Moon,
  Search,
  Settings,
  Sun,
  Upload,
} from 'lucide-react'
import ModuleNav from '../components/ModuleNav'
import type { AppModule } from '../store/useStore'

interface WorkbenchShellProps {
  activeModule: AppModule
  title: string
  subtitle?: string
  leftPanel: ReactNode
  centerPanel: ReactNode
  rightPanel?: ReactNode
  isDarkMode: boolean
  onModuleChange: (module: AppModule) => void
  onOpenUpload: () => void
  onOpenSearch: () => void
  onOpenExport: () => void
  onOpenNotes: () => void
  onOpenSettings: () => void
  onToggleDarkMode: () => void
}

export default function WorkbenchShell({
  activeModule,
  title,
  subtitle,
  leftPanel,
  centerPanel,
  rightPanel,
  isDarkMode,
  onModuleChange,
  onOpenUpload,
  onOpenSearch,
  onOpenExport,
  onOpenNotes,
  onOpenSettings,
  onToggleDarkMode,
}: WorkbenchShellProps) {
  return (
    <div className="h-screen overflow-hidden bg-gray-100 text-gray-950 dark:bg-gray-950 dark:text-gray-100">
      <div className="flex h-full min-w-0">
        <ModuleNav activeModule={activeModule} onModuleChange={onModuleChange} />

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-16 flex-shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-4 dark:border-gray-800 dark:bg-gray-900">
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold text-gray-950 dark:text-gray-100">
                {title}
              </h1>
              {subtitle && (
                <p className="truncate text-xs text-gray-500 dark:text-gray-400">
                  {subtitle}
                </p>
              )}
            </div>

            <div className="ml-auto flex items-center gap-2">
              <button
                onClick={onOpenUpload}
                className="hidden items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 md:flex"
              >
                <Upload className="h-4 w-4" />
                Add source
              </button>
              <IconButton
                label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                onClick={onToggleDarkMode}
              >
                {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </IconButton>
              <IconButton label="Settings" onClick={onOpenSettings}>
                <Settings className="h-5 w-5" />
              </IconButton>
              <button
                onClick={onOpenSearch}
                className="hidden items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 sm:flex"
                title="Search (Ctrl+K)"
              >
                <Search className="h-4 w-4" />
                Search
                <kbd className="hidden rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] font-mono text-gray-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-400 lg:inline">
                  Ctrl K
                </kbd>
              </button>
              <IconButton label="Export" onClick={onOpenExport}>
                <Download className="h-5 w-5" />
              </IconButton>
              <IconButton label="Notes" onClick={onOpenNotes}>
                <FileText className="h-5 w-5" />
              </IconButton>
            </div>
          </header>

          <main className="flex min-h-0 flex-1 overflow-hidden">
            <aside className="hidden min-h-0 flex-shrink-0 border-r border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900 lg:block">
              {leftPanel}
            </aside>

            <section className="min-w-0 flex-1 overflow-hidden">
              {centerPanel}
            </section>

            {rightPanel && (
              <aside className="hidden w-80 flex-shrink-0 border-l border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900 xl:block">
                {rightPanel}
              </aside>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

interface IconButtonProps {
  label: string
  onClick: () => void
  children: ReactNode
}

function IconButton({ label, onClick, children }: IconButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
      title={label}
      aria-label={label}
    >
      {children}
    </button>
  )
}
