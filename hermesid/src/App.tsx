import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './components/LandingPage'
import ResultPage from './components/ResultPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/score/:handle" element={<ResultPage />} />
      </Routes>
    </BrowserRouter>
  )
}
