'use client';

import React from 'react';
import { ChevronRight } from 'lucide-react';
import Link from 'next/link';

interface Breadcrumb {
  name: string;
  href?: string;
}

interface PageContainerProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Breadcrumb[];
  action?: React.ReactNode;
  children: React.ReactNode;
}

export default function PageContainer({
  title,
  subtitle,
  breadcrumbs,
  action,
  children,
}: PageContainerProps) {
  return (
    <div className="flex-1 p-6 md:p-8 overflow-y-auto">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          {/* Breadcrumbs */}
          {breadcrumbs && breadcrumbs.length > 0 && (
            <nav className="flex items-center space-x-1.5 text-xs font-semibold text-gray-400 mb-2">
              <Link href="/" className="hover:text-white transition-colors">
                Sentinel
              </Link>
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={idx}>
                  <ChevronRight className="h-3.5 w-3.5 text-gray-600" />
                  {crumb.href ? (
                    <Link href={crumb.href} className="hover:text-white transition-colors">
                      {crumb.name}
                    </Link>
                  ) : (
                    <span className="text-gray-300 font-bold">{crumb.name}</span>
                  )}
                </React.Fragment>
              ))}
            </nav>
          )}

          {/* Title and Subtitle */}
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-sm font-medium text-gray-400">
              {subtitle}
            </p>
          )}
        </div>

        {/* Action element */}
        {action && (
          <div className="flex items-center gap-3">
            {action}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <main className="w-full">
        {children}
      </main>
    </div>
  );
}
