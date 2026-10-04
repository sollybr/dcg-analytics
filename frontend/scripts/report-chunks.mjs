import fs from 'node:fs'
import path from 'node:path'

const dist = path.resolve('dist')
const LIMIT = 500 * 1024

function walk(dir) {
  const result = []

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name)

    if (entry.isDirectory()) {
      result.push(...walk(fullPath))
    } else {
      result.push(fullPath)
    }
  }

  return result
}

if (!fs.existsSync(dist)) {
  console.error(`dist directory not found: ${dist}`)
  process.exit(1)
}

const files = walk(dist)
  .filter(file => /\.(js|mjs|css)$/.test(file))
  .map(file => ({
    file: path.relative(dist, file),
    size: fs.statSync(file).size,
  }))
  .sort((a, b) => b.size - a.size)

console.log('\n=== Vite output chunks ===')

for (const file of files) {
  const kb = file.size / 1024
  const marker = file.size > LIMIT ? ' ⚠️' : ''

  console.log(
    `${kb.toFixed(1).padStart(10)} KB  ${file.file}${marker}`
  )
}

const large = files.filter(file => file.size > LIMIT)

console.log(`\nChunks > 500 KB: ${large.length}`)

if (large.length) {
  console.log('\nLarge chunks:')

  for (const file of large) {
    console.log(
      `  ${(file.size / 1024 / 1024).toFixed(2)} MB  ${file.file}`
    )
  }
}