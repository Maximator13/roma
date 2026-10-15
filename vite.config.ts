import { readFileSync } from 'node:fs'
import { defineConfig } from 'vitest/config'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { SITE } from './src/site.ts'

const BASIS_DIRECTORY = 'node_modules/three/examples/jsm/libs/basis/'
const BASIS_FILES = ['basis_transcoder.js', 'basis_transcoder.wasm']

function basisTranscoder(): Plugin {
  return {
    name: 'basis-transcoder',
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const file = BASIS_FILES.find((name) => request.url === `${SITE.base}basis/${name}`)
        if (!file) return next()
        response.setHeader('Content-Type', file.endsWith('.wasm') ? 'application/wasm' : 'text/javascript')
        response.end(readFileSync(BASIS_DIRECTORY + file))
      })
    },
  }
}

export default defineConfig({
  base: SITE.base,
  plugins: [react(), basisTranscoder()],
  build: {
    target: 'es2022',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1200,
  },
  test: {
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'],
  },
})
