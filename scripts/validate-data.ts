import { dataset } from '../src/data/index.ts'
import { validateDataset } from '../src/data/validate.ts'

const problems = validateDataset(dataset)

if (problems.length > 0) {
  console.error(problems.join('\n'))
  process.exit(1)
}

const counts = Object.entries(dataset).map(([name, items]) => `${items.length} ${name}`)
console.log(`Data valid: ${counts.join(', ')}.`)
