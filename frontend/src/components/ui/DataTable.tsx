import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { IconButton } from './IconButton';

export interface Column<T> {
  header: string;
  accessor?: keyof T;
  render?: (row: T, index: number) => React.ReactNode;
  className?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No records found.',
  onRowClick,
  isLoading = false,
}: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div className="w-full bg-slate-900/60 backdrop-blur-glass border border-slate-700/60 rounded-xl p-8 text-center text-slate-400 font-mono text-sm animate-pulse">
        Loading telemetry records...
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="w-full bg-slate-900/40 backdrop-blur-glass border border-slate-800 rounded-xl p-12 text-center">
        <p className="text-slate-400 font-mono text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-700/60 shadow-neo">
      <table className="neo-glass-table min-w-full">
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className={col.className}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick?.(row)}
              className={onRowClick ? 'cursor-pointer hover:bg-slate-800/60 transition-colors' : ''}
            >
              {columns.map((col, colIdx) => (
                <td key={colIdx} className={col.className}>
                  {col.render
                    ? col.render(row, rowIdx)
                    : col.accessor
                    ? String(row[col.accessor] ?? '')
                    : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalCount?: number;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  totalCount,
}) => {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between gap-4 py-3 px-2 text-xs text-slate-400 font-mono">
      <div>
        {totalCount !== undefined && <span>Total: {totalCount} items | </span>}
        <span>
          Page {currentPage} of {totalPages}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <IconButton
          icon={ChevronLeft}
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          ariaLabel="Previous page"
          size="sm"
        />
        <IconButton
          icon={ChevronRight}
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          ariaLabel="Next page"
          size="sm"
        />
      </div>
    </div>
  );
};
