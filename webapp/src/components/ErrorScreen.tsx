// webapp/src/components/ErrorScreen.tsx
//
// Full-screen error state with retry mechanism (D-30).
// Decision: pure presentation — retry callback provided by orchestrating hook (useSimulation in Plan 03-07).

interface ErrorScreenProps {
  message?: string;
  onRetry: () => void;
}

export function ErrorScreen({ message, onRetry }: ErrorScreenProps) {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center bg-dominant px-4"
      aria-label="Erreur de chargement"
    >
      <h1 className="text-xl font-semibold leading-tight text-primary mb-4">
        Impossible de charger les données.
      </h1>
      <p className="text-base font-normal leading-relaxed text-text-secondary mb-8 max-w-md text-center">
        {message ?? 'Vérifiez votre connexion internet et réessayez.'}
      </p>
      <button
        onClick={onRetry}
        className="bg-primary text-text-on-accent px-6 py-3 rounded-lg font-medium hover:opacity-90 focus:outline-2 focus:outline-offset-2 focus:outline-primary transition-opacity"
      >
        Réessayer
      </button>
    </div>
  );
}
