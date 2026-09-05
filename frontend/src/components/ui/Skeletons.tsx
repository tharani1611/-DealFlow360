import React from 'react';
import { GlassCard } from './GlassCard';

export const PageSkeleton: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto animate-pulse">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-white/10 rounded-lg"></div>
          <div className="h-4 w-72 bg-white/5 rounded"></div>
        </div>
        <div className="h-10 w-32 bg-white/10 rounded-xl"></div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="h-32 bg-white/5 rounded-xl border border-white/5"></div>
        <div className="h-32 bg-white/5 rounded-xl border border-white/5"></div>
        <div className="h-32 bg-white/5 rounded-xl border border-white/5"></div>
      </div>

      <div className="h-96 bg-white/5 rounded-xl border border-white/5"></div>
    </div>
  );
};

export const CardSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => {
  return (
    <GlassCard className="p-5 space-y-4 animate-pulse">
      <div className="h-6 w-1/3 bg-white/10 rounded"></div>
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-10 w-full bg-white/5 rounded-lg"></div>
        ))}
      </div>
    </GlassCard>
  );
};

export const TableSkeleton: React.FC<{ columns?: number; rows?: number }> = ({ columns = 5, rows = 5 }) => {
  return (
    <div className="w-full space-y-3 animate-pulse">
      <div className="flex gap-4 pb-2 border-b border-white/10">
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className="h-4 flex-1 bg-white/10 rounded"></div>
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-3 border-b border-white/5">
          {Array.from({ length: columns }).map((_, c) => (
            <div key={c} className="h-4 flex-1 bg-white/5 rounded"></div>
          ))}
        </div>
      ))}
    </div>
  );
};
