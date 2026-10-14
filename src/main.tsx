import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/cinzel/latin-400.css'
import '@fontsource/cinzel/latin-600.css'
import '@fontsource/eb-garamond/latin-400.css'
import '@fontsource/eb-garamond/latin-400-italic.css'
import '@fontsource/eb-garamond/latin-600.css'
import { App } from './App.tsx'
import './styles.css'

const root = document.getElementById('root')

if (root) {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
