import { expect, test } from 'claude-code/testing'

const PANE = { plugin: 'report-template-kit', component: 'Pane' as const, requestId: 'report-template-progress',
  props: { title: 'Report template', isFocused: false, bodyColumns: 80, placement: 'dock' as const,
    scroll: { offset: 0, bodyRows: 30 }, view: {} } }

test('traces report-template-kit steps in the status line and the pane', async ($, on) => {
  const seen: (string | undefined)[] = []
  on('ui.status', async (_$, e) => { seen.push(e.text); return { value: undefined } })
  let clock = 1_000_000
  on('clock.now', async () => ({ value: (clock += 7_000) }))
  on('ui.toast', async () => ({ value: undefined }))
  on('ui.open', async () => ({ value: { isPlaced: true } }) as never)
  on('skill.prompt', async (_$, e) => ({ text: e.text }))
  on('tool.call', async (_$, e) => ('command' in e && /BAD/.test(String(e.command))
    ? { result: 'x', text: 'BM04M.docx: 35/200 biến\nLỖI: engine: Invalid repeating row t1r3.', isError: true }
    : { result: 'ok' }) as never)

  const pane = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(JSON.stringify(await pane.drawn())).toContain('Chưa chạy')

  await $.skill.prompt({ skill: 'report-template-kit:report-to-docx-template', text: 'x' })
  expect(seen.at(-1)).toBe('📄 report-template · 1/8 B0 Chuẩn bị engine')

  await $.tool.call({ tool: 'Bash', command: 'python3 pdf_probe.py "../../KQKD_TNH_24-12-2024.pdf" --pages 1' })
  expect(seen.at(-1)).toBe('📄 report-template · 2/8 B1 Khảo sát PDF')

  await $.tool.call({ tool: 'Bash', command: 'python3 check_template.py ../BM04M_BAD.docx --mode multi_row' })
  expect(seen.at(-1)).toBe('📄 report-template · 7/8 B6 Kiểm tra engine ✗ còn lỗi')
  let drawn = JSON.stringify(await pane.drawn())
  expect(drawn).toContain('Invalid repeating row t1r3.')
  expect(drawn).toContain('Cần sửa: ')

  await $.tool.call({ tool: 'Bash', command: 'python3 check_template.py ../BM04M.docx --pdf' })
  expect(seen.at(-1)).toBe('📄 report-template · 7/8 B6 Kiểm tra engine ✓ đạt')

  const before = seen.length
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(seen.length).toBe(before)

  const desktop = await $.ui.mount({ ...PANE, surface: 'desktop' })
  for (const mounted of [pane, desktop]) {
    drawn = JSON.stringify(await mounted.drawn())
    expect(drawn).toContain('pdf_probe.py KQKD_TNH_24-12-2024.pdf')
    expect(drawn).toContain('check_template.py BM04M.docx')
    expect(drawn).toContain('Template: BM04M.docx')
    expect(drawn).toContain('7/8 ')
    expect(drawn).toContain('Upload lên /report-templates/')
  }
})
