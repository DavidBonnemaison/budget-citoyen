// webapp/src/pages/MethodologyPage.tsx
//
// Static methodology page with data source attribution (D-25, UI-08).
// Decision: niveau lycée reading level (D-26), short sentences, "vous" address.

import { Footer } from '../components/Footer';

export function MethodologyPage() {
  return (
    <div className="max-w-prose mx-auto py-12 px-6">
      <h1 className="text-3xl font-semibold leading-none text-primary mb-8">
        Méthodologie
      </h1>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-primary mb-3">
          Sources des données
        </h2>
        <p className="text-base leading-relaxed text-text-secondary mb-3">
          Le simulateur Budget Citoyen utilise des données publiques provenant de
          plusieurs sources officielles françaises.
        </p>
        <ul className="list-disc pl-6 space-y-2 text-base text-text-secondary">
          <li>
            <strong>Insee</strong> — Les données fiscales de référence proviennent
            des enquêtes Revenus Fiscaux de l&apos;Insee. Elles décrivent la
            répartition des revenus, des impôts et des prestations sociales dans
            la population française.
          </li>
          <li>
            <strong>budget.gouv.fr</strong> — Les paramètres budgétaires (taux
            d&apos;imposition, seuils, barèmes) sont issus de la Loi de Finances
            Initiale (LFI) 2025 publiée sur le site officiel du budget de l&apos;État.
          </li>
          <li>
            <strong>Modèle Mésange (Insee / Trésor)</strong> — Les projections
            macroéconomiques sont calculées à partir d&apos;une matrice des chocs
            dérivée du modèle Mésange, développé conjointement par l&apos;Insee
            et la Direction Générale du Trésor.
          </li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-primary mb-3">
          Fonctionnement du simulateur
        </h2>
        <p className="text-base leading-relaxed text-text-secondary mb-3">
          Le simulateur vous permet d&apos;explorer l&apos;impact de réformes
          budgétaires selon deux axes.
        </p>
        <p className="text-base leading-relaxed text-text-secondary mb-3">
          <strong>Les curseurs</strong> représentent cinq leviers budgétaires
          simplifiés : l&apos;impôt sur le revenu des ménages, l&apos;impôt sur les
          sociétés, la TVA, les cotisations sociales et les dépenses publiques.
          Vous pouvez les faire varier de −30 % à +30 % par rapport à leur
          valeur actuelle.
        </p>
        <p className="text-base leading-relaxed text-text-secondary mb-3">
          <strong>Les scénarios</strong> sont des combinaisons pré-calculées de
          curseurs. Quand vous sélectionnez un scénario, le simulateur affiche
          instantanément les résultats pour trois profils de foyers types. Quand
          vous déplacez les curseurs entre deux scénarios, les résultats sont
          interpolés pour estimer l&apos;impact de positions intermédiaires.
        </p>
        <p className="text-base leading-relaxed text-text-secondary">
          <strong>Les projections macroéconomiques</strong> sont obtenues par
          interpolation dans une matrice de chocs pré-calculée. Cette matrice
          indique, pour chaque combinaison de taux d&apos;imposition et de dépenses,
          l&apos;effet attendu sur le déficit, la dette, la croissance et l&apos;emploi
          à horizon de 5 ans.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-primary mb-3">
          Données synthétiques
        </h2>
        <p className="text-base leading-relaxed text-text-secondary mb-3">
          Pour protéger votre vie privée, le simulateur n&apos;utilise jamais vos
          données personnelles. Les impacts sur votre foyer sont calculés à
          partir de profils synthétiques représentatifs de la population
          française.
        </p>
        <p className="text-base leading-relaxed text-text-secondary">
          Ces profils sont générés statistiquement à partir des données de
          l&apos;Insee en appliquant des garanties de confidentialité
          différentielle. Aucune donnée personnelle réelle n&apos;est intégrée
          dans le simulateur et aucune donnée ne quitte votre navigateur.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-primary mb-3">
          Licence et contact
        </h2>
        <p className="text-base leading-relaxed text-text-secondary">
          Budget Citoyen est un simulateur open source publié sous licence
          compatible AGPL. Le code source est disponible publiquement.
          Pour toute question ou suggestion, vous pouvez contribuer directement
          au projet.
        </p>
      </section>

      <Footer />
    </div>
  );
}
