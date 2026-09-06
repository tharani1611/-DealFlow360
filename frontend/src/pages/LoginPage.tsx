import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authApi } from '../services/authApi';
import { GlassCard } from '../components/ui/GlassCard';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { BrutalButton } from '../components/ui/BrutalButton';
import { Shield, Eye, EyeOff, Lock, CheckCircle, Sparkles, Building2 } from 'lucide-react';

type RoleKey = 'admin' | 'sales_rep' | 'inventory_manager' | 'billing_controller';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Form State
  const [orgSlug, setOrgSlug] = useState('bulk-data-lab');
  const [selectedRole, setSelectedRole] = useState<RoleKey>('admin');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('admin_bulk-data-lab@dealflow360.com');
  const [password, setPassword] = useState('AdminPass123!');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const predictEmail = (role: RoleKey, slug: string) => {
    const slugKey = slug.trim().toLowerCase() || 'acme';
    let prefix = 'admin';
    if (role === 'sales_rep') prefix = 'sales';
    else if (role === 'inventory_manager') prefix = 'inventory';
    else if (role === 'billing_controller') prefix = 'billing';

    return `${prefix}_${slugKey}@dealflow360.com`;
  };

  const handleRoleChange = (role: RoleKey, currentSlug?: string) => {
    setSelectedRole(role);
    const activeSlug = currentSlug !== undefined ? currentSlug : orgSlug;
    const predicted = predictEmail(role, activeSlug);
    setEmail(predicted);

    // Set matching demo password if on bulk-data-lab
    if (activeSlug.trim().toLowerCase() === 'bulk-data-lab') {
      if (role === 'admin') setPassword('AdminPass123!');
      else if (role === 'sales_rep') setPassword('SalesPass123!');
      else if (role === 'inventory_manager') setPassword('InventoryPass123!');
      else if (role === 'billing_controller') setPassword('BillingPass123!');
    }
  };

  const handleSlugChange = (val: string) => {
    setOrgSlug(val);
    const predicted = predictEmail(selectedRole, val);
    setEmail(predicted);
  };

  const selectRolePreset = (role: RoleKey, slug: string = 'bulk-data-lab', presetPwd?: string, customEmail?: string) => {
    setOrgSlug(slug);
    setSelectedRole(role);
    const predictedEmail = customEmail || predictEmail(role, slug);
    setEmail(predictedEmail);

    if (presetPwd) {
      setPassword(presetPwd);
    } else if (slug === 'bulk-data-lab') {
      if (role === 'admin') setPassword('AdminPass123!');
      else if (role === 'sales_rep') setPassword('SalesPass123!');
      else if (role === 'inventory_manager') setPassword('InventoryPass123!');
      else if (role === 'billing_controller') setPassword('BillingPass123!');
    }
    setErrorMessage('');
  };

  const toggleMode = () => {
    const nextMode = !isRegisterMode;
    setIsRegisterMode(nextMode);
    setErrorMessage('');
    const predicted = predictEmail(selectedRole, orgSlug);
    setEmail(predicted);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    try {
      if (isRegisterMode) {
        if (!orgSlug.trim() || !email.trim() || !password) {
          throw new Error('Please enter Organization Slug, Role, Email, and Password.');
        }

        const tokenData = await authApi.register({
          organization_name: `Org ${orgSlug.trim()}`,
          organization_slug: orgSlug.trim().toLowerCase(),
          email: email.trim(),
          password,
          role: selectedRole,
          full_name: fullName.trim() || undefined,
        });

        await login(tokenData.access_token);
        showToast(`User registered and signed in as ${selectedRole.replace('_', ' ')}!`, 'success');
      } else {
        if (!orgSlug.trim() || !email.trim() || !password) {
          throw new Error('Please enter Organization Slug, Email, and Password.');
        }

        const tokenData = await authApi.login({
          organization_slug: orgSlug.trim().toLowerCase(),
          email: email.trim(),
          password,
        });
        await login(tokenData.access_token);
        showToast('Authenticated to Enterprise Workspace!', 'success');
      }
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.message || 'Authentication failed. Please check your tenant credentials.';
      setErrorMessage(msg);
      showToast(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4 relative overflow-hidden font-sans selection:bg-indigo-500 selection:text-white">
      {/* Neo Glass Ambient Lighting */}
      <div className="absolute top-1/4 left-1/3 w-[600px] h-[600px] bg-indigo-600/20 rounded-full blur-[160px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-1/4 right-1/3 w-[600px] h-[600px] bg-sky-600/15 rounded-full blur-[160px] pointer-events-none" />

      <div className="w-full max-w-lg z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-500/40 text-indigo-300 text-[11px] font-mono font-extrabold uppercase tracking-widest mb-3">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            ENTERPRISE EDITION v2.4.0
          </div>
          <div className="flex items-center justify-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600 border-2 border-indigo-400/50 shadow-neo flex items-center justify-center font-black text-white text-2xl">
              DF
            </div>
            <h1 className="text-4xl font-black text-slate-100 tracking-tight">DealFlow360</h1>
          </div>
          <p className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
            Autonomous Deal Governance & Multi-Tenant CRM Platform
          </p>
        </div>

        {/* Auth Card */}
        <GlassCard className="border-2 border-indigo-500/40 p-8 shadow-2xl relative overflow-hidden">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-black text-slate-100">
                {isRegisterMode ? 'New Tenant Registration' : 'Enterprise Workspace Sign In'}
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                {isRegisterMode ? 'Create new user persona within tenant' : 'Dynamic Role & Email Prediction Engine Active'}
              </p>
            </div>
            <button
              type="button"
              onClick={toggleMode}
              className="px-3 py-1.5 rounded-xl bg-indigo-950/80 border border-indigo-500/40 hover:bg-indigo-900 text-xs font-extrabold text-indigo-300 transition"
            >
              {isRegisterMode ? 'Sign In Instead' : 'Register New User'}
            </button>
          </div>

          {errorMessage && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-950/90 border border-rose-500/50 text-rose-200 text-xs font-semibold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <GlassInput
              label="Organization Slug (Tenant Key)"
              placeholder="e.g. bulk-data-lab, demo-enterprise, acme-corp"
              value={orgSlug}
              onChange={(e) => handleSlugChange(e.target.value)}
              helperText="Changing slug auto-predicts role email address below"
              required
            />

            <GlassSelect
              label="Role / Persona Selector"
              value={selectedRole}
              onChange={(e) => handleRoleChange(e.target.value as RoleKey)}
              options={[
                { value: 'admin', label: '👑 Admin / VP Sales' },
                { value: 'sales_rep', label: '💼 Sales Representative' },
                { value: 'inventory_manager', label: '📦 Inventory Manager' },
                { value: 'billing_controller', label: '💳 Billing Controller' },
              ]}
              helperText="Selecting role updates email prediction in real time"
            />

            {isRegisterMode && (
              <GlassInput
                label="Full Name (Optional)"
                placeholder="e.g. Jane Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            )}

            <div className="relative">
              <GlassInput
                label="Predicted Email Address"
                type="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                helperText="Predicted automatically based on slug & role (editable)"
                required
              />
              <div className="absolute right-3 top-9 text-[10px] font-mono text-emerald-400 font-bold px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 pointer-events-none">
                PREDICTED
              </div>
            </div>

            <div className="relative">
              <GlassInput
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                helperText="Enter tenant account password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-9 text-slate-400 hover:text-white text-xs p-1"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <div className="pt-2">
              <BrutalButton
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isLoading}
              >
                {isRegisterMode ? 'Complete Registration & Enter Workspace' : 'Sign In to Enterprise Workspace'}
              </BrutalButton>
            </div>
          </form>

          {/* Quick Role Prediction Presets */}
          {!isRegisterMode && (
            <div className="mt-5 pt-5 border-t border-slate-800/80">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[11px] font-bold text-slate-400 font-mono uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  1-Click Role Predictor & Demo Logins
                </span>
                <span className="text-[10px] font-mono text-indigo-400">Slug: {orgSlug || 'bulk-data-lab'}</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => selectRolePreset('admin')}
                  className={`px-3 py-2 rounded-xl border text-xs font-bold text-left transition flex flex-col ${
                    selectedRole === 'admin'
                      ? 'bg-indigo-600/30 border-indigo-400 text-indigo-200 shadow-neo'
                      : 'bg-slate-900/80 border-slate-800 hover:border-indigo-500/50 text-slate-300'
                  }`}
                >
                  <span className="text-indigo-300 flex items-center gap-1">👑 Admin</span>
                  <span className="text-[10px] text-slate-400 font-mono">admin_{orgSlug || 'bulk-data-lab'}@...</span>
                </button>

                <button
                  type="button"
                  onClick={() => selectRolePreset('sales_rep')}
                  className={`px-3 py-2 rounded-xl border text-xs font-bold text-left transition flex flex-col ${
                    selectedRole === 'sales_rep'
                      ? 'bg-sky-600/30 border-sky-400 text-sky-200 shadow-neo'
                      : 'bg-slate-900/80 border-slate-800 hover:border-sky-500/50 text-slate-300'
                  }`}
                >
                  <span className="text-sky-300 flex items-center gap-1">💼 Sales Rep</span>
                  <span className="text-[10px] text-slate-400 font-mono">sales_{orgSlug || 'bulk-data-lab'}@...</span>
                </button>

                <button
                  type="button"
                  onClick={() => selectRolePreset('inventory_manager')}
                  className={`px-3 py-2 rounded-xl border text-xs font-bold text-left transition flex flex-col ${
                    selectedRole === 'inventory_manager'
                      ? 'bg-emerald-600/30 border-emerald-400 text-emerald-200 shadow-neo'
                      : 'bg-slate-900/80 border-slate-800 hover:border-emerald-500/50 text-slate-300'
                  }`}
                >
                  <span className="text-emerald-300 flex items-center gap-1">📦 Inventory Manager</span>
                  <span className="text-[10px] text-slate-400 font-mono">inventory_{orgSlug || 'bulk-data-lab'}@...</span>
                </button>

                <button
                  type="button"
                  onClick={() => selectRolePreset('billing_controller')}
                  className={`px-3 py-2 rounded-xl border text-xs font-bold text-left transition flex flex-col ${
                    selectedRole === 'billing_controller'
                      ? 'bg-amber-600/30 border-amber-400 text-amber-200 shadow-neo'
                      : 'bg-slate-900/80 border-slate-800 hover:border-amber-500/50 text-slate-300'
                  }`}
                >
                  <span className="text-amber-300 flex items-center gap-1">💳 Billing Controller</span>
                  <span className="text-[10px] text-slate-400 font-mono">billing_{orgSlug || 'bulk-data-lab'}@...</span>
                </button>
              </div>

              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => selectRolePreset('admin', 'demo-enterprise', 'DemoPass123!', 'sales@dealflow.demo')}
                  className="flex-1 px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 hover:border-indigo-500 text-slate-200 text-xs font-bold text-center transition flex items-center justify-center gap-1.5"
                >
                  <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Switch Tenant: demo-enterprise</span>
                </button>
              </div>
            </div>
          )}

          {/* Enterprise Compliance Badges */}
          <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <CheckCircle className="w-3 h-3" /> ISO 27001 & SOC 2 Type II
            </span>
            <span className="flex items-center gap-1 text-indigo-400 font-bold">
              <Lock className="w-3 h-3" /> 256-Bit SSL Encrypted
            </span>
            <span className="flex items-center gap-1 text-sky-400 font-bold">
              <Shield className="w-3 h-3" /> Multi-Tenant
            </span>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
