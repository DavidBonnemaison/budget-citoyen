// webapp/src/components/SplashScreen.tsx
//
// Branded loading screen with phase-based progress tracking (D-27).
// Decision: pure presentation component — orchestration happens in useSimulation hook (Plan 03-07).

interface SplashProgress {
  phase: string;
  percent: number;
}

interface SplashScreenProps {
  progress: SplashProgress;
}

export function SplashScreen({ progress }: SplashScreenProps) {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center bg-dominant px-4"
      aria-label="Chargement du simulateur"
    >
      <h1 className="text-3xl font-semibold leading-none text-primary mb-6">
        Budget Citoyen
      </h1>
      <p className="text-base font-normal leading-relaxed text-text-secondary mb-8">
        Chargement du simulateur…
      </p>
      <div
        role="progressbar"
        aria-valuenow={Math.round(progress.percent)}
        aria-valuemin={0}
        aria-valuemax={100}
        className="w-64 h-2 bg-secondary rounded-full overflow-hidden"
      >
        <div
          className="h-full bg-primary rounded-full transition-all duration-300"
          style={{ width: `${progress.percent}%` }}
        />
      </div>
      <p className="text-sm font-normal leading-snug text-text-secondary mt-3">
        {progress.phase}
      </p>
    </div>
  );
}
