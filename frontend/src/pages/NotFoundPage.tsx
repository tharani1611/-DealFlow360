import React from 'react';
import { useNavigate } from 'react-router-dom';
import { HelpCircle, Home, ArrowLeft } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { BrutalButton } from '../components/ui/BrutalButton';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <GlassCard className="max-w-md w-full p-8 text-center border border-indigo-500/30">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center mx-auto mb-4 text-indigo-400">
          <HelpCircle className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-black text-white tracking-tight">404 — Page Not Found</h1>
        <p className="text-xs text-slate-300 mt-2 leading-relaxed">
          The requested URL path does not exist or has been moved within DealFlow360.
        </p>

        <div className="mt-6 flex items-center justify-center gap-3">
          <BrutalButton variant="secondary" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Go Back
          </BrutalButton>
          <BrutalButton variant="primary" onClick={() => navigate('/dashboard')}>
            <Home className="w-4 h-4 mr-1.5" /> Command Center
          </BrutalButton>
        </div>
      </GlassCard>
    </div>
  );
};
