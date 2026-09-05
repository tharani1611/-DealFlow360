import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authApi } from '../services/authApi';
import { GlassCard } from '../components/ui/GlassCard';
import { GlassInput } from '../components/ui/GlassInput';
import { BrutalButton } from '../components/ui/BrutalButton';
import { Shield, Eye, EyeOff } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Form State
  const [orgSlug, setOrgSlug] = useState('');
  const [orgName, setOrgName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    try {
      if (isRegisterMode) {
        if (!orgName.trim() || !orgSlug.trim() || !email.trim() || !password) {
          throw new Error('Please fill in all required registration fields.');
        }
        await register({
          organization_name: orgName.trim(),
          organization_slug: orgSlug.trim().toLowerCase(),
          email: email.trim(),
          password,
          full_name: fullName.trim() || undefined,
        });
        showToast('Organization and Admin User registered successfully!', 'success');
      } else {
        if (!orgSlug.trim() || !email.trim() || !password) {
          throw new Error('Please enter Organization Slug, Email, and Password.');
        }

        const formData = new URLSearchParams();
        formData.append('username', email.trim());
        formData.append('password', password);
        formData.append('organization_slug', orgSlug.trim().toLowerCase());

        const tokenData = await authApi.login(formData);
        await login(tokenData.access_token);
        showToast('Welcome back to DealFlow360!', 'success');
      }
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.message || 'Authentication failed. Please check your credentials.';
      setErrorMessage(msg);
      showToast(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4 relative overflow-hidden font-sans selection:bg-indigo-500 selection:text-white">
      {/* Neo Glass Ambient Lighting */}
      <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[150px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-1/4 right-1/3 w-[500px] h-[500px] bg-sky-600/15 rounded-full blur-[150px] pointer-events-none" />

      <div className="w-full max-w-md z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600 border-2 border-indigo-400/40 shadow-glass-glow mb-4">
            <span className="font-black text-2xl text-white tracking-tighter">DF360</span>
          </div>
          <h1 className="text-3xl font-black text-slate-100 tracking-tight">DealFlow360</h1>
          <p className="text-xs font-mono font-bold text-indigo-400 uppercase tracking-widest mt-1">
            Intelligent CRM for Sales Teams
          </p>
        </div>

        {/* Auth Card */}
        <GlassCard className="border-2 border-indigo-500/40 p-8 shadow-2xl">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
            <h2 className="text-lg font-black text-slate-100">
              {isRegisterMode ? 'Register Organization' : 'Welcome Back'}
            </h2>
            <button
              type="button"
              onClick={() => {
                setIsRegisterMode(!isRegisterMode);
                setErrorMessage('');
              }}
              className="text-xs font-bold text-indigo-400 hover:text-indigo-300 underline"
            >
              {isRegisterMode ? 'Sign In Instead' : 'Register New Org'}
            </button>
          </div>

          {errorMessage && (
            <div className="mb-6 p-3 rounded-lg bg-rose-950/80 border border-rose-500/50 text-rose-300 text-xs font-semibold">
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegisterMode && (
              <>
                <GlassInput
                  label="Organization Name"
                  placeholder="e.g. Acme Corporation"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  required
                />
                <GlassInput
                  label="Full Name"
                  placeholder="e.g. Jane Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </>
            )}

            <GlassInput
              label="Organization Slug"
              placeholder="e.g. acme-corp"
              value={orgSlug}
              onChange={(e) => setOrgSlug(e.target.value)}
              helperText="Your organization unique identifier"
              required
            />

            <GlassInput
              label="Email Address"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <div className="relative">
              <GlassInput
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
                {isRegisterMode ? 'Create Organization & Sign In' : 'Sign In to Dashboard'}
              </BrutalButton>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-500 flex items-center justify-center gap-1">
              <Shield className="w-3 h-3 text-emerald-400" /> Multi-Tenant Isolation & JWT Auth Secured
            </span>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
