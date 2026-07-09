import { Settings, X } from 'lucide-react'
import LLMSettingsPanel from './LLMSettingsPanel'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-800">
          <div className="flex items-center gap-3"><div className="rounded-lg bg-blue-50 p-2 dark:bg-blue-950"><Settings className="h-5 w-5 text-blue-600 dark:text-blue-300" /></div><div><h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Settings</h2><p className="text-xs text-gray-500 dark:text-gray-400">Local LLM configuration and safe runtime status</p></div></div>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-800" aria-label="Close settings"><X className="h-5 w-5 text-gray-500 dark:text-gray-400" /></button>
        </div>
        <div className="max-h-[calc(90vh-76px)] overflow-y-auto p-6"><LLMSettingsPanel /></div>
      </div>
    </div>
  )
}
