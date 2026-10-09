// Standalone Vitest configuration, kept separate from vite.config.js so
// that the app's build config never has to know about the test setup.
//
// Note on location: the project's test-writer boundary restricts this
// subagent to writing files under frontend/tests/ (and backend/tests/),
// so this config lives at frontend/tests/vitest.config.js rather than at
// the frontend root. Run it with:
//   npx vitest run --config tests/vitest.config.js   (from frontend/)
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Resolve the frontend/ directory (one level up from this file) so that
// `include`/`setupFiles` globs below resolve correctly regardless of the
// working directory `vitest` is invoked from.
const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

export default defineConfig({
  root: frontendRoot,
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.{js,jsx}'],
    setupFiles: ['./tests/setup.js'],
    globals: true,
  },
})
