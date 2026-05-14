// webapp/src/App.tsx
//
// Application shell: React Router + state machine (LOADING→PRESELECT→DISPLAYING→ERROR).
// Decision: BrowserRouter wrapping Routes for "/" and "/methodologie".
// Replaces the Plan 03-01 placeholder.

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useSimulation } from './hooks/useSimulation';
import { useServiceWorker } from './hooks/useServiceWorker';
import { SplashScreen } from './components/SplashScreen';
import { ErrorScreen } from './components/ErrorScreen';
import { SimulatorPage } from './pages/SimulatorPage';
import { MethodologyPage } from './pages/MethodologyPage';

function AppContent() {
  const simulation = useSimulation();
  const sw = useServiceWorker();

  if (simulation.phase === 'loading') {
    return <SplashScreen progress={simulation.loadProgress} />;
  }

  if (simulation.phase === 'error') {
    return (
      <ErrorScreen
        message={simulation.errorMessage ?? undefined}
        onRetry={simulation.retry}
      />
    );
  }

  return <SimulatorPage simulation={simulation} />;
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppContent />} />
        <Route path="/methodologie" element={<MethodologyPage />} />
      </Routes>
    </BrowserRouter>
  );
}
