import type { LanguagePreference } from './store/useStore'

type TranslationKey =
  | 'module.dashboard.title'
  | 'module.dashboard.subtitle'
  | 'module.workbench.title'
  | 'module.workbench.subtitle'
  | 'module.sources.title'
  | 'module.sources.subtitle'
  | 'module.notes.title'
  | 'module.notes.subtitle'
  | 'module.wiki.title'
  | 'module.wiki.subtitle'
  | 'module.outputs.title'
  | 'module.outputs.subtitle'
  | 'module.skills.title'
  | 'module.skills.subtitle'
  | 'module.agents.title'
  | 'module.agents.subtitle'
  | 'module.settings.title'
  | 'module.settings.subtitle'
  | 'nav.dashboard'
  | 'nav.workbench'
  | 'nav.sources'
  | 'nav.notes'
  | 'nav.wiki'
  | 'nav.outputs'
  | 'nav.skills'
  | 'nav.agents'
  | 'nav.settings'
  | 'shell.addSource'
  | 'shell.search'
  | 'shell.settings'
  | 'shell.export'
  | 'shell.notes'
  | 'shell.openSourceSelector'
  | 'shell.openInspector'
  | 'settings.language.title'
  | 'settings.language.description'
  | 'settings.language.label'
  | 'settings.language.english'
  | 'settings.language.chinese'
  | 'chat.readyTitle'
  | 'chat.readyDescription'
  | 'chat.noContext'
  | 'chat.selectedSources'
  | 'right.workspace'
  | 'right.preview'
  | 'right.subtitle'

const translations: Record<LanguagePreference, Record<TranslationKey, string>> = {
  en: {
    'module.dashboard.title': 'Dashboard',
    'module.dashboard.subtitle': 'Recent sources, model status, and workspace activity',
    'module.workbench.title': 'Workbench',
    'module.workbench.subtitle': 'Ask grounded questions across selected sources',
    'module.sources.title': 'Sources',
    'module.sources.subtitle': 'Manage local documents and source processing state',
    'module.notes.title': 'Notes',
    'module.notes.subtitle': 'Capture useful answers and source references',
    'module.wiki.title': 'Wiki',
    'module.wiki.subtitle': 'Source-grounded pages built from selected documents',
    'module.outputs.title': 'Outputs',
    'module.outputs.subtitle': 'Generated summaries, outlines, and study artifacts',
    'module.skills.title': 'Skills',
    'module.skills.subtitle': 'Local skill manifests with explicit safe tools',
    'module.agents.title': 'Agents',
    'module.agents.subtitle': 'Inspectable runs, steps, errors, and outputs',
    'module.settings.title': 'Settings',
    'module.settings.subtitle': 'Configure a local model connection and inspect safe runtime status',
    'nav.dashboard': 'Dashboard',
    'nav.workbench': 'Workbench',
    'nav.sources': 'Sources',
    'nav.notes': 'Notes',
    'nav.wiki': 'Wiki',
    'nav.outputs': 'Outputs',
    'nav.skills': 'Skills',
    'nav.agents': 'Agents',
    'nav.settings': 'Settings',
    'shell.addSource': 'Add source',
    'shell.search': 'Search',
    'shell.settings': 'Settings',
    'shell.export': 'Export',
    'shell.notes': 'Notes',
    'shell.openSourceSelector': 'Open source selector',
    'shell.openInspector': 'Open citation inspector',
    'settings.language.title': 'Interface language',
    'settings.language.description': 'Choose the language used by the Workbench shell and core controls.',
    'settings.language.label': 'Language',
    'settings.language.english': 'English',
    'settings.language.chinese': '中文',
    'chat.readyTitle': 'Ready to explore your sources',
    'chat.readyDescription': "Upload documents and ask questions. I'll provide answers with citations from your sources.",
    'chat.noContext': 'No context selected',
    'chat.selectedSources': 'Selected sources',
    'right.workspace': 'Workspace',
    'right.preview': 'Preview',
    'right.subtitle': 'Tools, artifacts, evidence, notes, and runtime context',
  },
  'zh-CN': {
    'module.dashboard.title': '仪表盘',
    'module.dashboard.subtitle': '最近来源、模型状态和工作区活动',
    'module.workbench.title': '工作台',
    'module.workbench.subtitle': '基于已选来源进行有依据的问答',
    'module.sources.title': '来源',
    'module.sources.subtitle': '管理本地文档和处理状态',
    'module.notes.title': '笔记',
    'module.notes.subtitle': '保存有用回答和来源引用',
    'module.wiki.title': '知识库',
    'module.wiki.subtitle': '从已选文档构建有依据的页面',
    'module.outputs.title': '产物',
    'module.outputs.subtitle': '生成摘要、大纲和学习材料',
    'module.skills.title': '技能',
    'module.skills.subtitle': '本地技能清单和明确的安全工具边界',
    'module.agents.title': '智能体',
    'module.agents.subtitle': '可检查的运行、步骤、错误和产物',
    'module.settings.title': '设置',
    'module.settings.subtitle': '配置本地模型连接并查看安全运行状态',
    'nav.dashboard': '仪表盘',
    'nav.workbench': '工作台',
    'nav.sources': '来源',
    'nav.notes': '笔记',
    'nav.wiki': '知识库',
    'nav.outputs': '产物',
    'nav.skills': '技能',
    'nav.agents': '智能体',
    'nav.settings': '设置',
    'shell.addSource': '添加来源',
    'shell.search': '搜索',
    'shell.settings': '设置',
    'shell.export': '导出',
    'shell.notes': '笔记',
    'shell.openSourceSelector': '打开来源选择器',
    'shell.openInspector': '打开工作区面板',
    'settings.language.title': '界面语言',
    'settings.language.description': '选择工作台外壳和核心控件使用的语言。',
    'settings.language.label': 'Language',
    'settings.language.english': 'English',
    'settings.language.chinese': '中文',
    'chat.readyTitle': '开始探索你的来源',
    'chat.readyDescription': '上传文档并提问，系统会基于来源给出带引用的回答。',
    'chat.noContext': '未选择上下文',
    'chat.selectedSources': '已选来源',
    'right.workspace': '工作区',
    'right.preview': '预览',
    'right.subtitle': '工具、产物、证据、笔记和运行状态',
  },
}

export function t(language: LanguagePreference, key: TranslationKey) {
  return translations[language][key]
}
