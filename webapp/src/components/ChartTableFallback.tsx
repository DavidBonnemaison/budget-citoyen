// webapp/src/components/ChartTableFallback.tsx
//
// Screen-reader-only HTML table for chart data (A11Y-02).
// Decision: provides equivalent data for non-visual users per RGAA 4 Thématique 8.

interface ChartTableFallbackProps {
  title: string;
  data: Array<Record<string, unknown>>;
}

export function ChartTableFallback({ title, data }: ChartTableFallbackProps) {
  if (data.length === 0) return null;

  const columns = Object.keys(data[0]);

  return (
    <table className="sr-only" aria-label={`Données tabulaires : ${title}`}>
      <caption>{title}</caption>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col} scope="col">
              {col}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            {columns.map((col) => (
              <td key={col}>{String(row[col])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
