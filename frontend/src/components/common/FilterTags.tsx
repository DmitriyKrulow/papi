// frontend/src/components/common/FilterTags.tsx
import { X } from 'lucide-react';

export interface FilterTag {
  id: string;
  label: string;
  color?: string;
}

interface FilterTagsProps {
  tags: FilterTag[];
  activeTagIds: string[];
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
  className?: string;
}

const FilterTags = ({ tags, activeTagIds, onToggle, onRemove, className = '' }: FilterTagsProps) => {
  if (tags.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-1.5 ${className}`}>
      {tags.map(tag => {
        const isActive = activeTagIds.includes(tag.id);
        return (
          <span
            key={tag.id}
            onClick={() => onToggle(tag.id)}
            className={`
              inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium cursor-pointer transition-all duration-200
              ${isActive
                ? `bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300 ring-1 ring-brand-200 dark:ring-brand-800`
                : 'bg-gray-100 text-gray-500 dark:bg-graphite-800 dark:text-graphite-400 hover:bg-gray-200 dark:hover:bg-graphite-700'
              }
            `}
          >
            <span>{tag.label}</span>
            {isActive && (
              <X
                onClick={(e) => { e.stopPropagation(); onRemove(tag.id); }}
                className="w-3 h-3 cursor-pointer hover:text-red-500 transition-colors"
              />
            )}
          </span>
        );
      })}
    </div>
  );
};

export default FilterTags;
