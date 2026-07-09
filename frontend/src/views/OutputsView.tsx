import { FileText, ListChecks, Sparkles } from 'lucide-react'
import type { AppModule } from '../store/useStore'

interface OutputsViewProps {
  onModuleChange: (module: AppModule) => void
}

export default function OutputsView({ onModuleChange }: OutputsViewProps) {
  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-5xl space-y-6">
        <section className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-100">Outputs</h2>
              <p className="mt-1 max-w-2xl text-sm leading-relaxed text-gray-500 dark:text-gray-400">
                Generated artifacts will live here: summaries, paper outlines, review cards, quizzes, and knowledge-base reports.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <RoadmapCard
            icon={<FileText className="h-5 w-5" />}
            title="Summaries"
            description="Generate source-grounded summaries from selected documents."
          />
          <RoadmapCard
            icon={<ListChecks className="h-5 w-5" />}
            title="Review sets"
            description="Turn materials into study questions, flashcards, and quizzes."
          />
          <RoadmapCard
            icon={<Sparkles className="h-5 w-5" />}
            title="Writing plans"
            description="Build paper outlines with claims, evidence, and citation anchors."
          />
        </section>

        <section className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-900">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">No generated outputs yet</p>
          <p className="mx-auto mt-2 max-w-lg text-xs leading-relaxed text-gray-500 dark:text-gray-400">
            Start in the workbench with selected sources. Output generation will be added after the shell and answer-quality phases are stable.
          </p>
          <button
            onClick={() => onModuleChange('workbench')}
            className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Open workbench
          </button>
        </section>
      </div>
    </div>
  )
}

interface RoadmapCardProps {
  icon: React.ReactNode
  title: string
  description: string
}

function RoadmapCard({ icon, title, description }: RoadmapCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-100">{title}</h3>
      <p className="mt-1 text-xs leading-relaxed text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  )
}
