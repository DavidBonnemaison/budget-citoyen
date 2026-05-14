// webapp/src/main.tsx
//
// React 19 entry point — mounts <App /> into the DOM.
// Uses createRoot (React 18+ concurrent root) for useTransition support.

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('Root element not found');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
