// webapp/src/components/ImpactPill.tsx
//
// Single household profile impact pill with ±€/mois display (D-04, D-06).
// Decision: color-coded (green positive, red negative, dash empty) for scannability.

interface ImpactPillProps {
  label: string;
  income: string;
  impact: number | null;
}

export function ImpactPill({ label, income, impact }: ImpactPillProps) {
  const formatter = new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    signDisplay: 'always',
    maximumFractionDigits: 0,
  });

  const impactText =
    impact !== null ? `${formatter.format(impact).replace('€', '')}€/mois` : null;

  const impactColor =
    impact === null
      ? 'text-text-disabled'
      : impact >= 0
        ? 'text-emerald-700'
        : 'text-red-700';

  const ariaLabel = impactText
    ? `${label}: ${impactText}`
    : `${label}: données non disponibles`;

  return (
    <div
      className="flex flex-col items-center justify-center p-4 rounded-lg bg-secondary min-h-[88px] min-w-[140px]"
      aria-label={ariaLabel}
    >
      <span className="text-sm text-text-secondary">{label}</span>
      <span className="text-xs text-text-disabled">{income}</span>
      {impact !== null ? (
        <span className={`text-lg font-semibold mt-1 ${impactColor}`}>
          {impactText}
        </span>
      ) : (
        <span className="text-3xl font-light text-text-disabled mt-1">—</span>
      )}
    </div>
  );
}
