import { EmptyState } from "./EmptyState";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => string | number;
};

type DataTableProps<T> = {
  columns: Array<DataTableColumn<T>>;
  emptyMessage: string;
  rows: T[];
};

export function DataTable<T>({ columns, emptyMessage, rows }: DataTableProps<T>) {
  if (rows.length === 0) {
    return <EmptyState title="No rows available" message={emptyMessage} />;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column.key}>{column.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
