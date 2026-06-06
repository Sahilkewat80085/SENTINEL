'use client';

import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  className?: string;
  footer?: React.ReactNode;
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  className,
  footer
}: ModalProps) {
  // Disable body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 animate-fade-in"
        onClick={onClose}
      />
      
      {/* Modal Dialog */}
      <div 
        className={cn(
          "relative flex flex-col w-full max-w-lg overflow-hidden rounded-xl border border-card-border bg-card shadow-2xl glow-primary z-10 transition-transform duration-300 animate-scale-in",
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-card-border/60 bg-[#111726]/40 p-4">
          <h3 className="text-lg font-bold tracking-wide text-white">
            {title}
          </h3>
          <button 
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-card-border hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 text-sm text-gray-300">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 border-t border-card-border/60 bg-[#111726]/20 p-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
