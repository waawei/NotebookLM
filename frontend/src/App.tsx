import { useEffect, useState } from 'react'
import ExportModal from './components/ExportModal'
import NotesModal from './components/NotesModal'
import RightInspector from './components/RightInspector'
import SearchModal from './components/SearchModal'
import SettingsModal from './components/SettingsModal'
import Sidebar from './components/Sidebar'
import Toast from './components/Toast'
import UploadModal from './components/UploadModal'
import WorkbenchShell from './layouts/WorkbenchShell'
import DashboardView from './views/DashboardView'
import NotesView from './views/NotesView'
import OutputsView from './views/OutputsView'
import SettingsView from './views/SettingsView'
import SourcesView from './views/SourcesView'
import WorkbenchView from './views/WorkbenchView'
import { useStore } from './store/useStore'
import type { AppModule } from './store/useStore'

const moduleCopy: Record<AppModule, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Dashboard',
    subtitle: 'Recent sources, model status, and workspace activity',
  },
  workbench: {
    title: 'Workbench',
    subtitle: 'Ask grounded questions across selected sources',
  },
  sources: {
    title: 'Sources',
    subtitle: 'Manage local documents and source processing state',
  },
  notes: {
    title: 'Notes',
    subtitle: 'Capture useful answers and source references',
  },
  outputs: {
    title: 'Outputs',
    subtitle: 'Generated summaries, outlines, and study artifacts',
  },
  settings: {
    title: 'Settings',
    subtitle: 'Read-only runtime configuration from backend .env',
  },
}

function App() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [isNotesModalOpen, setIsNotesModalOpen] = useState(false)
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const {
    activeModule,
    setActiveModule,
    toasts,
    removeToast,
    isDarkMode,
    toggleDarkMode,
  } = useStore()

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDarkMode])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setIsSearchModalOpen(true)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleModuleChange = (module: AppModule) => {
    setActiveModule(module)
  }

  const activeCopy = moduleCopy[activeModule]

  const renderCenterPanel = () => {
    if (activeModule === 'dashboard') {
      return (
        <DashboardView
          onOpenUpload={() => setIsUploadModalOpen(true)}
          onOpenSettings={() => setIsSettingsModalOpen(true)}
          onModuleChange={handleModuleChange}
        />
      )
    }

    if (activeModule === 'sources') {
      return <SourcesView onOpenUpload={() => setIsUploadModalOpen(true)} />
    }

    if (activeModule === 'notes') {
      return <NotesView onOpenNotesModal={() => setIsNotesModalOpen(true)} />
    }

    if (activeModule === 'outputs') {
      return <OutputsView onModuleChange={handleModuleChange} />
    }

    if (activeModule === 'settings') {
      return <SettingsView />
    }

    return <WorkbenchView />
  }

  return (
    <>
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>

      <WorkbenchShell
        activeModule={activeModule}
        title={activeCopy.title}
        subtitle={activeCopy.subtitle}
        isDarkMode={isDarkMode}
        onModuleChange={handleModuleChange}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        onOpenSearch={() => setIsSearchModalOpen(true)}
        onOpenExport={() => setIsExportModalOpen(true)}
        onOpenNotes={() => setIsNotesModalOpen(true)}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        onToggleDarkMode={toggleDarkMode}
        leftPanel={
          <Sidebar
            isCollapsed={isSidebarCollapsed}
            onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            onUploadClick={() => setIsUploadModalOpen(true)}
          />
        }
        centerPanel={renderCenterPanel()}
        rightPanel={<RightInspector />}
      />

      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
      />

      <NotesModal
        isOpen={isNotesModalOpen}
        onClose={() => setIsNotesModalOpen(false)}
      />

      <SearchModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
      />

      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
      />
    </>
  )
}

export default App
