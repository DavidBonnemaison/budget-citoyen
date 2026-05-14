// webapp/src/hooks/useSliderWithUrl.ts
//
// Slider drag → URL state sync hook (D-15, D-23).
// Decision: calls pushState() on drag-end to encode slider positions as URL query param.

import { useCallback } from 'react';
import { pushState, decodeState } from '../state/url-codec';
import type { URLState } from '../state/types';

export function useSliderWithUrl() {
  const getInitialState = useCallback((): URLState | null => {
    const params = new URLSearchParams(window.location.search);
    const encoded = params.get('state');
    if (!encoded) return null;
    return decodeState(encoded);
  }, []);

  const syncState = useCallback((state: URLState) => {
    pushState(state);
  }, []);

  return { getInitialState, syncState };
}
