export const PAGE_IDS = ['mentions-legales', 'confidentialite', 'conditions', 'sources'] as const

export type PageId = (typeof PAGE_IDS)[number]

export type Route =
  | { name: 'home' }
  | { name: 'event'; id: string }
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
  if (section && isPageId(section) && id === undefined) return { name: 'page', id: section }
  return { name: 'not-found', path }
}

export function routeToHash(route: Route): string {
  switch (route.name) {
    case 'home':
      return '#/'
    case 'event':
      return `#/evenement/${route.id}`
    case 'page':
      return `#/${route.id}`
    case 'not-found':
      return `#/${route.path}`
  }
}
