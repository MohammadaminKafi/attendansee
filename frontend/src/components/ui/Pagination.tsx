import React from 'react';
import { Button } from './Button';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  className = '',
}) => {
  const pages: number[] = [];
  
  // Generate page numbers with ellipsis
  const addPage = (page: number) => {
    if (!pages.includes(page) && page >= 1 && page <= totalPages) {
      pages.push(page);
    }
  };

  // Always show first page
  addPage(1);

  // Show pages around current page
  for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
    addPage(i);
  }

  // Always show last page
  if (totalPages > 1) {
    addPage(totalPages);
  }

  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div className="text-sm text-slate-400">
        Page {currentPage} of {totalPages}
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          Previous
        </Button>

        <div className="hidden sm:flex items-center gap-1">
          {pages.map((page, index) => {
            // Add ellipsis if there's a gap
            const showEllipsisBefore = index > 0 && page > pages[index - 1] + 1;
            
            return (
              <React.Fragment key={page}>
                {showEllipsisBefore && (
                  <span className="px-2 text-slate-500">...</span>
                )}
                <button
                  onClick={() => onPageChange(page)}
                  className={`
                    px-3 py-1 rounded text-sm font-medium transition-colors
                    ${
                      page === currentPage
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                    }
                  `}
                >
                  {page}
                </button>
              </React.Fragment>
            );
          })}
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next
        </Button>
      </div>
    </div>
  );
};
