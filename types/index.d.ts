export type StepKey = 'B0' | 'B1' | 'B2' | 'B3' | 'B4' | 'B5' | 'B6' | 'B7'

/** One traced action: a script Claude ran or a confirmation the user gave. */
export type LogEntry = {
  /** ms since the run started */
  at: number
  step: StepKey
  /** what ran, e.g. "check_template.py BM04M.docx" */
  text: string
  /** null while running */
  ok: boolean | null
  /** short outcome: error line, chosen answer... */
  note: string
}

export type Progress = {
  /** step in progress; null until the skill or one of its scripts runs */
  current: StepKey | null
  /** result of the last check_template.py run */
  check: 'ok' | 'fail' | null
  /** template file the last check ran on */
  template: string
  /** $.clock.now() when the run started */
  startedAt: number
  /** last outcome per step, shown beside it */
  details: Partial<Record<StepKey, string>>
  /** newest last, at most 12 */
  log: LogEntry[]
}

declare module 'claude-code' {
  interface PluginState {
    'report-template-kit': { progress: Progress }
  }
}
