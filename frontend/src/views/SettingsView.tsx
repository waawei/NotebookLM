import LLMSettingsPanel from '../components/LLMSettingsPanel'
import { t } from '../i18n'
import { useStore, type LanguagePreference } from '../store/useStore'

export default function SettingsView() {
  const { language, setLanguage } = useStore()

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-5xl space-y-4">
        <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                {t(language, 'settings.language.title')}
              </h2>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t(language, 'settings.language.description')}
              </p>
            </div>
            <label className="block min-w-48">
              <span className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">
                {t(language, 'settings.language.label')}
              </span>
              <select
                aria-label="Language"
                value={language}
                onChange={(event) => setLanguage(event.target.value as LanguagePreference)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-950 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
              >
                <option value="en">{t(language, 'settings.language.english')}</option>
                <option value="zh-CN">{t(language, 'settings.language.chinese')}</option>
              </select>
            </label>
          </div>
        </section>
        <LLMSettingsPanel />
      </div>
    </div>
  )
}
