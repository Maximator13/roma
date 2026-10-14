import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { SITE } from './src/site.ts'

export default defineConfig({
  base: SITE.base,
  plugins: [react()],
  build: {
    target: 'es2022',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1200,
  },
  test: {
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'],
  },
})
