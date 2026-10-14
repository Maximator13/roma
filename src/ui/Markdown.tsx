import { marked } from 'marked'
import { useMemo } from 'react'
import { frenchSpacing } from '../core/typography.ts'

marked.use({
  renderer: {
    link({ href, text }) {
      const external = /^https?:/.test(href)
      const attributes = external ? ' target="_blank" rel="noopener noreferrer"' : ''
      return `<a href="${href}"${attributes}>${text}</a>`
    },
  },
})

export function Markdown({ source, className }: { source: string; className?: string }) {
  const html = useMemo(() => marked.parse(frenchSpacing(source), { async: false }), [source])
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />
}
