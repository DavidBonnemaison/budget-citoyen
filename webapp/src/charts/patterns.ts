// webapp/src/charts/patterns.ts
//
// SVG pattern definitions for the 4 macro trajectory chart series.
// Decision: D-19 — pattern fills differentiate series for RGAA 4 A11Y-03 compliance
//   (never rely on color alone). Each pattern uses a distinct geometric style paired
//   with its deuteranopia-safe Wong 2011 palette color.
//
// Usage: Inject into a global <svg><defs> element via vega-embed's patch option
//   or as a persistent <svg> element in the DOM (RESEARCH.md lines 897-906).

export const CHART_PATTERNS_SVG = `
<defs>
  <pattern id="pattern-deficit" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="8" stroke="#0072B2" stroke-width="1.5" opacity="0.5"/>
  </pattern>
  <pattern id="pattern-debt" width="6" height="6" patternUnits="userSpaceOnUse">
    <circle cx="3" cy="3" r="1.5" fill="#E69F00" opacity="0.5"/>
  </pattern>
  <pattern id="pattern-gdp" width="8" height="8" patternUnits="userSpaceOnUse">
    <line x1="0" y1="0" x2="8" y2="8" stroke="#009E73" stroke-width="1" opacity="0.5"/>
    <line x1="8" y1="0" x2="0" y2="8" stroke="#009E73" stroke-width="1" opacity="0.5"/>
  </pattern>
  <pattern id="pattern-employment" width="6" height="6" patternUnits="userSpaceOnUse">
    <rect x="0" y="0" width="2" height="6" fill="#CC79A7" opacity="0.5"/>
  </pattern>
</defs>`;
