import LLMSettingsPanel from '../components/LLMSettingsPanel'

export default function SettingsView() {
  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-5xl">
        <LLMSettingsPanel />
      </div>
    </div>
  )
}
