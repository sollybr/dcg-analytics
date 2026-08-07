import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

import { Analytics } from "@vercel/analytics/react"

import './App.css'
import './Dashboard.css'
import Dashboard from './Dashboard'

function App() {
  return (
    <div className="App">
      <Dashboard />
      <Analytics />
    </div>
  )
}

export default App