// webapp/src/state/url-codec.ts
//
// URL state encoding/decoding for shareable simulation links (D-23).
// Decision: base64-encoded JSON with strict runtime type validation.
// Pattern 5 from RESEARCH.md: encodeURIComponent → btoa, decode with null-return error handling.

import type { URLState, SliderState } from './types';

// ── Validation Helpers ────────────────────────────────────────────────────────

function isValidSliderState(value: unknown): value is SliderState {
  if (typeof value !== 'object' || value === null) return false;
  const p = value as Record<string, unknown>;
  return (
    typeof p.ir === 'number' &&
    typeof p.is === 'number' &&
    typeof p.tva === 'number' &&
    typeof p.cotisations === 'number' &&
    typeof p.depenses === 'number'
  );
}

function isValidURLState(value: unknown): value is URLState {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  if (!('s' in obj)) return false;
  if (!('p' in obj) || !isValidSliderState(obj.p)) return false;
  if (typeof obj.f !== 'number') return false;
  if (typeof obj.a !== 'boolean') return false;
  return true;
}

// ── Encode ────────────────────────────────────────────────────────────────────

export function encodeState(state: URLState): string {
  const json = JSON.stringify(state);
  const uriEncoded = encodeURIComponent(json);
  return btoa(unescape(uriEncoded));
}

// ── Decode ────────────────────────────────────────────────────────────────────

export function decodeState(encoded: string): URLState | null {
  if (!encoded) return null;
  try {
    const uriDecoded = decodeURIComponent(escape(atob(encoded)));
    const parsed: unknown = JSON.parse(uriDecoded);
    if (!isValidURLState(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

// ── Push to URL ───────────────────────────────────────────────────────────────

export function pushState(state: URLState): void {
  const encoded = encodeState(state);
  const url = new URL(window.location.href);
  url.searchParams.set('state', encoded);
  window.history.replaceState(null, '', url.toString());
}
