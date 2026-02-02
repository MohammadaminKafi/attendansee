import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, Layers, Sparkles, Users, Wand2, UserCheck } from 'lucide-react';

interface ActionItem {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  isProcessing?: boolean;
}

interface ActionCategory {
  label: string;
  items: ActionItem[];
}

interface ActionsMenuProps {
  categories: ActionCategory[];
}

export const ActionsMenu: React.FC<ActionsMenuProps> = ({ categories }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative inline-block" ref={menuRef}>
      {/* Menu Button */}
      <button
        className="flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors shadow-lg font-medium"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>Actions</span>
        <ChevronDown className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className="absolute top-full left-0 mt-2 bg-dark-card border border-dark-border rounded-lg shadow-2xl z-50"
        >
          <div className="p-4 grid grid-cols-3 gap-6 min-w-[900px]">
            {categories.map((category) => (
              <div key={category.label} className="flex flex-col">
                {/* Category Header */}
                <div className="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-dark-border mb-2">
                  {category.label}
                </div>

                {/* Category Items */}
                <div className="flex-1">
                  {category.items.length === 0 ? (
                    <div className="px-2 py-3 text-sm text-gray-500 italic">
                      No actions available
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {category.items.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => {
                            if (!item.disabled && !item.isProcessing) {
                              item.onClick();
                              setIsOpen(false);
                            }
                          }}
                          disabled={item.disabled || item.isProcessing}
                          className={`w-full px-3 py-3 flex items-start gap-3 hover:bg-dark-hover transition-colors text-left rounded-md ${
                            item.disabled || item.isProcessing
                              ? 'opacity-50 cursor-not-allowed'
                              : 'cursor-pointer'
                          }`}
                        >
                          {/* Icon */}
                          <div className="mt-0.5 flex-shrink-0">
                            {item.isProcessing ? (
                              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
                            ) : (
                              <div className="text-primary">{item.icon}</div>
                            )}
                          </div>

                          {/* Label and Description */}
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-white mb-0.5">
                              {item.label}
                            </div>
                            <div className="text-xs text-gray-400 leading-relaxed">
                              {item.description}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Export icons for use in parent components
export { Layers, Sparkles, Users, Wand2, UserCheck };
