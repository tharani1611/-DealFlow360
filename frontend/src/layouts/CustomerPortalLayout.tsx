import React from 'react';
import { Outlet } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

export const CustomerPortalLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-neo-bg flex flex-col">
      <header className="bg-glass-base backdrop-blur-glass border-b border-glass-border px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center font-black text-slate-900 text-lg shadow-neo-sm">
            CP
          </div>
          <div>
            <h1 className="font-bold text-slate-100 text-sm">DealFlow360 Customer Portal</h1>
            <span className="text-[10px] text-slate-400">Secure Proposal Inspection & Negotiation</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/60 px-3 py-1.5 rounded-full border border-emerald-500/30">
          <ShieldCheck className="w-4 h-4" />
          <span className="font-mono">Token Encrypted Session</span>
        </div>
      </header>

      <main className="flex-1 p-8 max-w-6xl w-full mx-auto">
        <Outlet />
      </main>
    </div>
  );
};
