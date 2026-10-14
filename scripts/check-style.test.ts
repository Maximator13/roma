import { describe, expect, it } from 'vitest'
import { commentProblem } from './check-style.ts'

describe('commentProblem', () => {
  it('flags line and block comments in scripts', () => {
    expect(commentProblem('a.ts', 'const a = 1 // note\n')).toBe(true)
    expect(commentProblem('a.tsx', 'const b = <div>{/* note */}</div>\n')).toBe(true)
    expect(commentProblem('a.ts', '/* header */\nexport {}\n')).toBe(true)
  })

  it('ignores comment markers inside strings, templates, regexes and JSX text', () => {
    expect(commentProblem('a.ts', "const url = 'https://example.org/a'\n")).toBe(false)
    expect(commentProblem('a.ts', 'const t = `a // b /* c */`\n')).toBe(false)
    expect(commentProblem('a.ts', String.raw`const r = /\/\//g`)).toBe(false)
    expect(commentProblem('a.tsx', 'const l = <a href="https://x.org">https://x.org</a>\n')).toBe(false)
  })

  it('handles css, markup and yaml', () => {
    expect(commentProblem('a.css', 'a { color: red; } /* x */')).toBe(true)
    expect(commentProblem('a.css', "a { background: url('data:image/svg+xml;utf8,/*') }")).toBe(false)
    expect(commentProblem('a.html', '<!-- x --><p>a</p>')).toBe(true)
    expect(commentProblem('a.yml', 'name: deploy # x')).toBe(true)
    expect(commentProblem('a.yml', "url: 'https://a.org/#x'")).toBe(false)
  })
})
