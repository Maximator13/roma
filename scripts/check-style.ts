import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

const forbiddenDash = new RegExp(`[${String.fromCharCode(0x2013, 0x2014)}]`)
const textFile = /\.(ts|tsx|js|mjs|cjs|json|md|html|css|svg|yml|yaml|txt|py|glsl)$/
const scriptFile = /\.(ts|tsx|js|mjs|cjs)$/
const hashCommentFile = /\.(ya?ml|py)$/

function listedFiles(): string[] {
  const output = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard'], { encoding: 'utf8' })
  return output.split('\n').filter((file) => textFile.test(file))
}

function scriptKindOf(file: string): ts.ScriptKind {
  if (file.endsWith('.tsx')) return ts.ScriptKind.TSX
  if (file.endsWith('.ts')) return ts.ScriptKind.TS
  return ts.ScriptKind.JS
}

function hasScriptComment(file: string, text: string): boolean {
  const sourceFile = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, scriptKindOf(file))
  const hasCommentAround = (node: ts.Node) =>
    (ts.getLeadingCommentRanges(text, node.pos)?.length ?? 0) > 0 ||
    (ts.getTrailingCommentRanges(text, node.end)?.length ?? 0) > 0
  const visit = (node: ts.Node): boolean => hasCommentAround(node) || node.getChildren(sourceFile).some(visit)
  return visit(sourceFile)
}

function withoutQuotedText(line: string): string {
  return line.replace(/"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, '""')
}

function hasHashComment(text: string): boolean {
  return text.split('\n').some((line) => /(^|\s)#/.test(withoutQuotedText(line)))
}

function hasCssComment(text: string): boolean {
  return withoutQuotedText(text).includes('/*')
}

function hasMarkupComment(text: string): boolean {
  return text.includes('<!--')
}

export function commentProblem(file: string, text: string): boolean {
  if (scriptFile.test(file)) return hasScriptComment(file, text)
  if (hashCommentFile.test(file)) return hasHashComment(text)
  if (file.endsWith('.css')) return hasCssComment(text)
  if (file.endsWith('.html') || file.endsWith('.svg')) return hasMarkupComment(text)
  return false
}

function problemsIn(file: string): string[] {
  const text = readFileSync(file, 'utf8')
  const problems: string[] = []
  text.split('\n').forEach((line, index) => {
    if (forbiddenDash.test(line)) problems.push(`${file}:${index + 1}: em or en dash`)
  })
  if (commentProblem(file, text)) problems.push(`${file}: comment in code`)
  return problems
}

function main() {
  const problems = listedFiles().flatMap(problemsIn)
  if (problems.length > 0) {
    console.error(problems.join('\n'))
    process.exit(1)
  }
  console.log('Style check passed.')
}

if (import.meta.main) main()
