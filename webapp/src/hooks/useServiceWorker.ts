// webapp/src/hooks/useServiceWorker.ts
//
// Service Worker registration and update lifecycle (D-31).
// Decision: graceful degradation when SW not supported — isReady=true, no errors.

import { useState, useEffect } from 'react';

interface ServiceWorkerState {
  isReady: boolean;
  hasUpdate: boolean;
}

export function useServiceWorker(): ServiceWorkerState {
  const [isReady, setIsReady] = useState(false);
  const [hasUpdate, setHasUpdate] = useState(false);

  useEffect(() => {
    // Skip Service Worker in dev mode — cached assets interfere with HMR
    // and every code change requires cache clearing.
    if (import.meta.env.DEV) {
      setIsReady(true);
      return;
    }

    if (!('serviceWorker' in navigator)) {
      setIsReady(true);
      return;
    }

    let canceled = false;

    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        if (canceled) return;

        if (registration.active) {
          setIsReady(true);
        }

        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (!newWorker) return;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              setHasUpdate(true);
            }
          });
        });
      })
      .catch(() => {
        if (!canceled) setIsReady(true);
      });

    const handleActive = () => {
      if (!canceled) setIsReady(true);
    };
    const handleUpdate = () => {
      if (!canceled) setHasUpdate(true);
    };

    navigator.serviceWorker.addEventListener('controllerchange', handleActive);

    return () => {
      canceled = true;
      navigator.serviceWorker.removeEventListener('controllerchange', handleActive);
    };
  }, []);

  return { isReady, hasUpdate };
}
