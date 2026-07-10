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
import { t } from '../i18n'
import { useStore, type AppModule } from '../store/useStore'

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
  const language = useStore((state) => state.language)

  return (
    <div data-testid="workbench-shell" className="h-screen overflow-hidden bg-[#f8f7f6] text-[#1a1a2e] dark:bg-gray-950 dark:text-gray-100">
      <div className="flex h-full min-w-0">
        <ModuleNav activeModule={activeModule} onModuleChange={onModuleChange} />

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-16 flex-shrink-0 items-center gap-4 border-b border-[#dddcd9] bg-white px-4 dark:border-gray-800 dark:bg-gray-900">
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
              <details className="relative lg:hidden">
                <summary aria-label={t(language, 'shell.openSourceSelector')} className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 [&::-webkit-details-marker]:hidden">
                  <FileText className="h-5 w-5" />
                </summary>
                <div data-testid="mobile-source-panel" className="fixed right-3 top-16 z-50 max-h-[calc(100vh-5rem)] w-72 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-xl dark:border-gray-800 dark:bg-gray-900 lg:hidden">
                  {leftPanel}
                </div>
              </details>
              {rightPanel && (
                <details className="relative xl:hidden">
                  <summary aria-label={t(language, 'shell.openInspector')} className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 [&::-webkit-details-marker]:hidden">
                    <Search className="h-5 w-5" />
                  </summary>
                  <div data-testid="mobile-inspector" className="fixed right-3 top-16 z-50 max-h-[calc(100vh-5rem)] w-80 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-xl dark:border-gray-800 dark:bg-gray-900 xl:hidden">
                    {rightPanel}
                  </div>
                </details>
              )}
              <button
                onClick={onOpenUpload}
                className="hidden items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 md:flex"
              >
                <Upload className="h-4 w-4" />
                {t(language, 'shell.addSource')}
              </button>
              <IconButton
                label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                onClick={onToggleDarkMode}
              >
                {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </IconButton>
              <IconButton label={t(language, 'shell.settings')} onClick={onOpenSettings}>
                <Settings className="h-5 w-5" />
              </IconButton>
              <button
                onClick={onOpenSearch}
                className="hidden items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 sm:flex"
                title="Search (Ctrl+K)"
              >
                <Search className="h-4 w-4" />
                {t(language, 'shell.search')}
                <kbd className="hidden rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] font-mono text-gray-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-400 lg:inline">
                  Ctrl K
                </kbd>
              </button>
              <IconButton label={t(language, 'shell.export')} onClick={onOpenExport}>
                <Download className="h-5 w-5" />
              </IconButton>
              <IconButton label={t(language, 'shell.notes')} onClick={onOpenNotes}>
                <FileText className="h-5 w-5" />
              </IconButton>
            </div>
          </header>

          <main className="flex min-h-0 flex-1 overflow-hidden">
            <aside data-testid="desktop-left-panel" className="hidden min-h-0 flex-shrink-0 border-r border-[#dddcd9] bg-[#f1f0ef] dark:border-gray-800 dark:bg-gray-900 lg:block">
              {leftPanel}
            </aside>

            <section data-testid="center-panel" className="min-w-0 flex-1 overflow-hidden bg-white dark:bg-gray-950">
              {centerPanel}
            </section>

            {rightPanel && (
              <aside className="hidden w-80 flex-shrink-0 border-l border-[#dddcd9] bg-[#f1f0ef] dark:border-gray-800 dark:bg-gray-900 xl:block">
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
