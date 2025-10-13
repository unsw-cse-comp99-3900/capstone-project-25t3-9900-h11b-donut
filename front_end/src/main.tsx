import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { installErrorGuards } from './setupErrorGuards'
import './index.css'
import App from './App.tsx'

installErrorGuards();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
