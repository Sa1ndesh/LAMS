import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (row: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (row: T) => string | number;
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function Table<T>({
  data,
  columns,
  keyExtractor,
  isLoading = false,
  emptyMessage = 'No records found',
  className,
}: TableProps<T>) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-lams-border bg-lams-surface shadow-card">
      <table className={twMerge(clsx('w-full text-left border-collapse text-sm', className))}>
        <thead>
          <tr className="bg-slate-50 border-b border-lams-border text-xs font-semibold text-lams-muted uppercase tracking-wider">
            {columns.map((col, index) => (
              <th key={index} className={clsx('px-6 py-3.5', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-lams-border bg-white">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-8 text-center text-lams-muted">
                <div className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-lams-secondary" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading table data...
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-8 text-center text-lams-muted">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr key={keyExtractor(row)} className="hover:bg-slate-50/80 transition-colors">
                {columns.map((col, index) => (
                  <td key={index} className={clsx('px-6 py-4 text-lams-dark', col.className)}>
                    {col.cell ? col.cell(row) : col.accessorKey ? (row[col.accessorKey] as React.ReactNode) : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

