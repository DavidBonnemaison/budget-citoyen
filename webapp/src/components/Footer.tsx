// webapp/src/components/Footer.tsx
//
// Persistent footer with methodology link (D-25).
// Decision: uses <a> not <Link> — router integration happens in Plan 03-07.

export function Footer() {
  return (
    <footer className="border-t border-gray-200 pt-6 mt-12 px-6 pb-8 text-sm text-text-secondary">
      <div className="flex justify-between items-center max-w-5xl mx-auto">
        <a
          href="/methodologie"
          className="hover:text-primary underline underline-offset-2 transition-colors focus:outline-2 focus:outline-offset-2 focus:outline-primary"
        >
          Méthodologie et sources
        </a>
        <span>Budget Citoyen © 2025</span>
      </div>
    </footer>
  );
}
