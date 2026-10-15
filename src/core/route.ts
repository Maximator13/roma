export const PAGE_IDS = ['mentions-legales', 'confidentialite', 'conditions', 'sources'] as const

export type PageId = (typeof PAGE_IDS)[number]

export type Route =
  | { name: 'home' }
  | { name: 'event'; id: string }
  | { name: 'scene'; id: string }
  | { name: 'page'; id: PageId }
  | { name: 'not-found'; path: string }

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

function isPageId(value: string): value is PageId {
  return (PAGE_IDS as readonly string[]).includes(value)
}

export function parseHash(hash: string): Route {
  const path = decodeURIComponent(hash.replace(/^#/, '')).replace(/^\/+|\/+$/g, '')
  if (path === '') return { name: 'home' }
  const [section, id, ...rest] = path.split('/')
  if (section === 'evenement' && id && SLUG.test(id) && rest.length === 0) return { name: 'event', id }
  if (section === 'scene' && id && SLUG.test(id) && rest.length === 0) return { name: 'scene', id }
  if (section && isPageId(section) && id === undefined) return { name: 'page', id: section }
  return { name: 'not-found', path }
}

export function routeToHash(route: Route): string {
  switch (route.name) {
    case 'home':
      return '#/'
    case 'event':
      return `#/evenement/${route.id}`
    case 'scene':
      return `#/scene/${route.id}`
    case 'page':
      return `#/${route.id}`
    case 'not-found':
      return `#/${route.path}`
  }
}

export function routeFromLocation(pathname: string, hash: string, base: string): Route {
  if (hash.replace(/^#\/?/, '') !== '') return parseHash(hash)
  const path = pathname.startsWith(base) ? pathname.slice(base.length) : ''
  return path.replace(/\/+$/, '') === '' || path === 'index.html' ? { name: 'home' } : parseHash(`#/${path}`)
}

export function internalRoute(href: string, base: string): Route | null {
  const hash = href.startsWith('#/') ? href : href.startsWith(`${base}#/`) ? href.slice(base.length) : null
  return hash === null ? null : parseHash(hash)
}
