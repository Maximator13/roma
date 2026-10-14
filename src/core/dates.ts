export type Year = number
export type Side = 'bc' | 'ad'
export type Precision = 'day' | 'month' | 'year' | 'decade' | 'century'

export interface HistoricalYear {
  year: number
  side: Side
}

export interface DatedItem {
  start: Year
  end?: Year
  month?: number
  day?: number
  precision: Precision
}

export const FIRST_YEAR: Year = -752
export const LAST_YEAR: Year = 1453

const MONTHS = [
  'janvier',
  'février',
  'mars',
  'avril',
  'mai',
  'juin',
  'juillet',
  'août',
  'septembre',
  'octobre',
  'novembre',
  'décembre',
]

const BC_SUFFIX = 'av. J.-C.'
const AD_SUFFIX = 'apr. J.-C.'

export function fromHistorical(year: number, side: Side): Year {
  if (!Number.isInteger(year) || year < 1) throw new RangeError(`Invalid historical year: ${year}`)
  return side === 'bc' ? 1 - year : year
}

export function toHistorical(year: Year): HistoricalYear {
  return year <= 0 ? { year: 1 - year, side: 'bc' } : { year, side: 'ad' }
}

export function yearsBetween(start: Year, end: Year): number {
  return end - start
}

function needsAdSuffix(year: Year): boolean {
  return year > 0 && year < 100
}

function suffixOf(year: Year): string {
  if (year <= 0) return BC_SUFFIX
  return needsAdSuffix(year) ? AD_SUFFIX : ''
}

function withSuffix(text: string, suffix: string): string {
  return suffix ? `${text} ${suffix}` : text
}

export function formatYear(year: Year): string {
  return withSuffix(String(toHistorical(year).year), suffixOf(year))
}

export function formatRange(start: Year, end: Year): string {
  const startSuffix = suffixOf(start)
  const endSuffix = suffixOf(end)
  const startText = String(toHistorical(start).year)
  const endText = withSuffix(String(toHistorical(end).year), endSuffix)
  const sharedSuffix = startSuffix === endSuffix
  return `de ${sharedSuffix ? startText : withSuffix(startText, startSuffix)} à ${endText}`
}

export function centuryOf(year: Year): { century: number; side: Side } {
  const historical = toHistorical(year)
  return { century: Math.ceil(historical.year / 100), side: historical.side }
}

const ROMAN_DIGITS: [number, string][] = [
  [1000, 'M'],
  [900, 'CM'],
  [500, 'D'],
  [400, 'CD'],
  [100, 'C'],
  [90, 'XC'],
  [50, 'L'],
  [40, 'XL'],
  [10, 'X'],
  [9, 'IX'],
  [5, 'V'],
  [4, 'IV'],
  [1, 'I'],
]

export function romanNumeral(value: number): string {
  let rest = value
  let text = ''
  for (const [amount, digits] of ROMAN_DIGITS) {
    while (rest >= amount) {
      text += digits
      rest -= amount
    }
  }
  return text
}

export function formatCentury(year: Year): string {
  const { century, side } = centuryOf(year)
  const ordinal = century === 1 ? 'Ier' : `${romanNumeral(century)}e`
  const suffix = side === 'bc' ? BC_SUFFIX : century === 1 ? AD_SUFFIX : ''
  return withSuffix(`${ordinal} siècle`, suffix)
}

function monthName(month: number | undefined): string {
  const name = month === undefined ? undefined : MONTHS[month - 1]
  if (!name) throw new RangeError(`Invalid month: ${month}`)
  return name
}

function formatDay(day: number | undefined): string {
  if (day === undefined) throw new RangeError('Missing day')
  return day === 1 ? '1er' : String(day)
}

export function formatDate(item: DatedItem): string {
  if (item.end !== undefined && item.end !== item.start) return formatRange(item.start, item.end)
  switch (item.precision) {
    case 'day':
      return `${formatDay(item.day)} ${monthName(item.month)} ${formatYear(item.start)}`
    case 'month':
      return `${monthName(item.month)} ${formatYear(item.start)}`
    case 'year':
      return formatYear(item.start)
    case 'decade':
      return `vers ${formatYear(item.start)}`
    case 'century':
      return formatCentury(item.start)
  }
}
