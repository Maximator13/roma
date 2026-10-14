import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export const base = '/roma/'

export default defineConfig({
  base,
  plugins: [react()],
  build: {
    target: 'es2022',
    assetsInlineLimit: 0,
  },
  test: {
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'],
  },
})
