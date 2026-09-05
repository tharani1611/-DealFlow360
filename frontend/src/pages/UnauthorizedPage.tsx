import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, Home } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { BrutalButton } from '../components/ui/BrutalButton';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <GlassCard className="max-w-md w-full p-8 text-center border border-rose-500/30">
        <div className="w-16 h-16 rounded-2xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center mx-auto mb-4 text-rose-400">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-black text-white tracking-tight">403 — Access Restricted</h1>
        <p className="text-xs text-slate-300 mt-2 leading-relaxed">
          You do not have administrative permissions or role authority to view this page or perform this operation.
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
