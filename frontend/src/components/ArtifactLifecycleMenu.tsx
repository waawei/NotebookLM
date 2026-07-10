import { useState } from 'react'
import type { ReactNode } from 'react'
import { Archive, Download, Eye, MoreHorizontal, RotateCcw } from 'lucide-react'
import type { OutputItem } from '../services/api'

interface ArtifactLifecycleMenuProps {
  output: OutputItem
  onPreview: () => void
  onExport: () => void
  onArchive: () => void
  onRestore: () => void
}

export default function ArtifactLifecycleMenu({
  output,
  onPreview,
  onExport,
  onArchive,
  onRestore,
}: ArtifactLifecycleMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const isArchived = output.status === 'archived'

  const runAction = (action: () => void) => {
    setIsOpen(false)
    action()
  }

  return (
    <div className="relative flex-shrink-0">
      <button
        type="button"
        aria-label={`Artifact actions for ${output.title}`}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={(event) => {
          event.stopPropagation()
          setIsOpen((current) => !current)
        }}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-[#e2e1de] bg-white text-slate-500 hover:bg-[#f5f4f3] hover:text-slate-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-1 w-36 rounded-lg border border-[#e2e1de] bg-white p-1 shadow-lg dark:border-gray-700 dark:bg-gray-900"
          onClick={(event) => event.stopPropagation()}
        >
          <MenuItem icon={<Eye className="h-3.5 w-3.5" />} label="Preview" onClick={() => runAction(onPreview)} />
          <MenuItem icon={<Download className="h-3.5 w-3.5" />} label="Export" onClick={() => runAction(onExport)} />
          {isArchived ? (
            <MenuItem icon={<RotateCcw className="h-3.5 w-3.5" />} label="Restore" onClick={() => runAction(onRestore)} />
          ) : (
            <MenuItem icon={<Archive className="h-3.5 w-3.5" />} label="Archive" onClick={() => runAction(onArchive)} />
          )}
        </div>
      )}
    </div>
  )
}

function MenuItem({ icon, label, onClick }: { icon: ReactNode; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs font-medium text-slate-700 hover:bg-[#f5f4f3] dark:text-slate-200 dark:hover:bg-gray-800"
    >
      {icon}
      {label}
    </button>
  )
}
