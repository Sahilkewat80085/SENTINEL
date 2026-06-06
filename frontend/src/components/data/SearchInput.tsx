import React from 'react';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onSearchChange: (value: string) => void;
  containerClassName?: string;
}

export default function SearchInput({
  onSearchChange,
  containerClassName,
  className,
  placeholder = 'Search...',
  ...props
}: SearchInputProps) {
  return (
    <div className={cn("relative w-full", containerClassName)}>
      <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-500">
        <Search className="h-4 w-4" />
      </div>
      <input
        type="text"
        placeholder={placeholder}
        onChange={(e) => onSearchChange(e.target.value)}
        className={cn(
          "w-full rounded-lg border border-card-border bg-card py-2 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none transition-all duration-150",
          className
        )}
        {...props}
      />
    </div>
  );
}
