import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { LogEntry, Progress, StepKey } from '../types'

const PANE = 'report-template-progress'
const TITLE = 'Report template'
const SKILL = /report-to-docx-template|report-template(?!-progress)/
const LOG_SIZE = 12

type Step = { label: string; does: string; next: string }
const STEPS: Record<StepKey, Step> = {
  B0: { label: 'Chuẩn bị engine', does: 'Trích engine Superset từ values YAML vào customsso/',
    next: 'Khảo sát PDF mẫu bằng pdf_probe.py' },
  B1: { label: 'Khảo sát PDF', does: 'Đọc bố cục, cột, toạ độ số của báo cáo mẫu',
    next: 'Đề xuất loại template và chờ anh/chị xác nhận' },
  B2: { label: 'Xác nhận loại', does: 'Người dùng chọn per_row / multi_row / dashboard và cách group',
    next: 'Đặt tên biến theo data-contract.md' },
  B3: { label: 'Đặt tên biến', does: 'Tên biến {#...#} = tên cột dataset',
    next: 'Dựng file .docx bằng build.js' },
  B4: { label: 'Dựng template', does: 'Sinh file .docx từ docx_kit.js',
    next: 'Sinh dữ liệu mẫu, đặc tả Excel và SQL' },
  B5: { label: 'Dữ liệu & SQL', does: 'Dữ liệu mẫu từ PDF, Cau_truc_du_lieu.xlsx, file SQL',
    next: 'Điền thử bằng check_template.py --pdf' },
  B6: { label: 'Kiểm tra engine', does: 'Điền thử bằng đúng code Superset, xuất PDF so với bản gốc',
    next: 'Upload lên /report-templates/ và cấu hình report' },
  B7: { label: 'Triển khai Superset', does: 'Upload, mapping, group/repeat rows, export',
    next: 'Hoàn tất' },
}
const KEYS = Object.keys(STEPS) as StepKey[]

// Bash command -> step it belongs to
const SCRIPTS: ReadonlyArray<readonly [RegExp, StepKey]> = [
  [/sync_engine\.py/, 'B0'],
  [/pdf_probe\.py/, 'B1'],
  [/node\s+build\w*\.js/, 'B4'],
  [/(outputs|multi_data|make_data)\.py/, 'B5'],
  [/check_template\.py/, 'B6'],
]
const SCRIPT_NAME = /[\w-]+\.(py|js)\b/
const FILE_ARG = /([^\s"'/]+\.(pdf|docx|yaml|json))\b/

const EMPTY: Progress = { current: null, check: null, template: '', startedAt: 0, details: {}, log: [] }
const progress = atom({ plugin: 'report-template-kit', key: 'progress' } as const, EMPTY)

const base = (path: string): string => path.split('/').pop() ?? path
const clip = (text: string, max: number): string => (text.length > max ? `${text.slice(0, max - 1)}…` : text)

function elapsed(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000))
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m${String(s % 60).padStart(2, '0')}s`
}

function bar(done: number, total: number, width = 16): string {
  const fill = Math.round((done / total) * width)
  return '█'.repeat(fill) + '░'.repeat(width - fill)
}

/** What the command ran, for the trace: "check_template.py BM04M.docx" */
function describe(command: string): string {
  const script = command.match(SCRIPT_NAME)?.[0] ?? command.slice(0, 30)
  const file = command.match(FILE_ARG)?.[1]
  return file ? `${script} ${base(file)}` : script
}

/** First error line of a failed run (check_template prints "LỖI: ...") */
function failure(text: string | undefined): string {
  const line = (text ?? '').split('\n').find(l => /LỖI|Error|error/.test(l)) ?? 'lệnh trả lỗi'
  return clip(line.replace(/^.*?LỖI:\s*/, '').trim(), 60)
}

/** Answers out of the AskUserQuestion result text: "Q"="A" */
function answers(text: string | undefined): string {
  const found = [...(text ?? '').matchAll(/"[^"]*"="([^"]*)"/g)].map(m => m[1])
  return clip(found.join(', ') || 'đã trả lời', 60)
}

function statusText(p: Progress): string {
  const step = p.current ?? 'B0'
  const tail = step === 'B6' && p.check ? (p.check === 'ok' ? ' ✓ đạt' : ' ✗ còn lỗi') : ''
  return `📄 report-template · ${KEYS.indexOf(step) + 1}/8 ${step} ${STEPS[step].label}${tail}`
}

async function enter($: EngineInterface, step: StepKey, change: (p: Progress) => Partial<Progress> = () => ({})): Promise<Progress> {
  const before = await read($, progress)
  const now = await $.clock.now()
  const next = await update($, progress, p => ({ ...p, ...(p.current === null ? { startedAt: now } : {}), ...change(p), current: step }))
  $.ui.status(statusText(next))
  if (before.current === null) {
    $.ui.toast('report-template-kit đang chạy · /report-template-progress để xem chi tiết')
    void $.ui.open({ id: PANE, title: TITLE })
  }
  return next
}

async function trace($: EngineInterface, step: StepKey, text: string): Promise<number> {
  const p = await enter($, step)
  const at = (await $.clock.now()) - p.startedAt
  await update($, progress, q => ({ ...q, log: [...q.log, { at, step, text, ok: null, note: '' }].slice(-LOG_SIZE) }))
  return at
}

async function settle($: EngineInterface, at: number, ok: boolean, note: string, step: StepKey): Promise<void> {
  await update($, progress, p => ({
    ...p,
    log: p.log.map(l => (l.at === at && l.ok === null ? { ...l, ok, note } : l)),
    details: { ...p.details, [step]: note },
  }))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'report-template-progress', description: 'Mở panel tiến độ report-template-kit (B0–B7)' })
    return next(e)
  })

  on('command.run', { command: 'report-template-progress' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE })
    return { text: 'Đã mở panel tiến độ report-template-kit.' }
  })

  on('skill.prompt', async ($, e, next) => {
    if (SKILL.test(e.skill)) {
      const p = await read($, progress)
      // a finished run starts over; a run in progress keeps its trace
      if (p.check === 'ok') await update($, progress, () => EMPTY)
      await enter($, 'B0')
    }
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    if (e.tool === 'AskUserQuestion') {
      if ((await read($, progress)).current === null) return next(e)
      const at = await trace($, 'B2', 'Hỏi xác nhận loại template')
      const ran = await next(e)
      await settle($, at, ran.deny === undefined && ran.isError !== true, ran.deny ? 'chưa trả lời' : answers(ran.text), 'B2')
      return ran
    }
    if (e.tool !== 'Bash') return next(e)
    const step = SCRIPTS.find(([re]) => re.test(e.command))?.[1]
    if (!step) return next(e)
    const text = describe(e.command)
    if (step === 'B6') await enter($, 'B6', () => ({ template: base(e.command.match(FILE_ARG)?.[1] ?? ''), check: null }))
    const at = await trace($, step, text)
    const ran = await next(e)
    const ok = ran.deny === undefined && ran.isError !== true
    await settle($, at, ok, ok ? (step === 'B6' ? 'template đạt' : 'xong') : failure(ran.deny ?? ran.text), step)
    if (step === 'B6') await enter($, 'B6', () => ({ check: ok ? 'ok' : 'fail' }))
    return ran
  }).catch(($, e, next) => next(e)) // a broken indicator never blocks a tool call

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const p = await read($, progress)
    if (p.current === null) {
      return (
        <Box flexDirection="column" paddingX={1}>
          <Text bold color="claude">Report Template Kit</Text>
          <Text dimColor>Chưa chạy. Gõ /report-template &lt;file PDF&gt; để bắt đầu.</Text>
        </Box>
      )
    }
    const at = KEYS.indexOf(p.current)
    const failed = p.current === 'B6' && p.check === 'fail'
    const passed = p.current === 'B6' && p.check === 'ok'
    const done = at + (passed ? 1 : 0)
    const width = Math.max(30, (e.props.bodyColumns ?? 60) - 2)
    const now = (await $.clock.now()) - p.startedAt
    const icon = (i: number): [string, string] =>
      i < at || (i === at && passed) ? ['✓', 'success'] : i > at ? ['○', 'inactive'] : failed ? ['✗', 'error'] : ['▶', 'claude']

    return (
      <Box flexDirection="column" paddingX={1}>
        <Box justifyContent="space-between">
          <Text bold color="claude">Report Template Kit</Text>
          <Text dimColor>{`⏱ ${elapsed(now)}`}</Text>
        </Box>
        <Text>
          <Text color={failed ? 'error' : 'success'}>{bar(done, KEYS.length)}</Text>
          <Text bold>{` ${done}/${KEYS.length} `}</Text>
          <Text color={failed ? 'error' : 'claude'}>{`${p.current} ${STEPS[p.current].label}`}</Text>
        </Text>
        {p.template !== '' && <Text dimColor>{`Template: ${p.template}`}</Text>}

        <Box flexDirection="column" marginTop={1}>
          {KEYS.map((k, i) => {
            const [mark, color] = icon(i)
            const detail = p.details[k]
            return (
              <Box flexDirection="column" key={k}>
                <Text wrap="truncate-end">
                  <Text color={color}>{`${mark} `}</Text>
                  <Text bold={i === at} dimColor={i > at}>{`${k} ${STEPS[k].label.padEnd(20)}`}</Text>
                  {detail !== undefined && <Text color={i === at && failed ? 'error' : 'subtle'}>{clip(detail, width - 26)}</Text>}
                </Text>
                {i === at && <Text dimColor italic wrap="wrap">{`   ${STEPS[k].does}`}</Text>}
              </Box>
            )
          })}
        </Box>

        <Box flexDirection="column" marginTop={1}>
          <Text bold>Nhật ký</Text>
          {p.log.length === 0 && <Text dimColor>Chưa có lệnh nào.</Text>}
          {p.log.slice(-8).map((l: LogEntry) => (
            <Text wrap="truncate-end" key={`${l.at}`}>
              <Text dimColor>{`+${elapsed(l.at).padEnd(7)}`}</Text>
              <Text color="suggestion">{`${l.step} `}</Text>
              <Text>{clip(l.text, Math.max(12, width - 30))}</Text>
              <Text color={l.ok === null ? 'warning' : l.ok ? 'success' : 'error'}>{l.ok === null ? '  … đang chạy' : l.ok ? '  ✓' : '  ✗'}</Text>
              {l.ok === false && <Text color="error">{` ${l.note}`}</Text>}
            </Text>
          ))}
        </Box>

        <Box marginTop={1} borderStyle="round" borderColor={failed ? 'error' : 'subtle'} paddingX={1}>
          <Text wrap="wrap">
            <Text bold color={failed ? 'error' : 'claude'}>{failed ? 'Cần sửa: ' : 'Tiếp theo: '}</Text>
            <Text>{failed ? 'xem dòng ✗ trong nhật ký, sửa template/dữ liệu rồi chạy lại check_template.py' : STEPS[passed ? 'B6' : p.current].next}</Text>
          </Text>
        </Box>
      </Box>
    )
  })
}
