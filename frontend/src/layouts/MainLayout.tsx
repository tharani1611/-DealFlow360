import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UserCheck,
  Package,
  FileText,
  TrendingUp,
  Clock,
  Sparkles,
  Settings,
  LogOut,
  Menu,
  Building2,
  ChevronRight,
  Bell,
  ShieldCheck,
  BarChart3,
  Workflow,
  Warehouse,
  CreditCard,
  Repeat,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { GlassDrawer } from '../components/ui/GlassDrawer';
import { NotificationDrawer } from '../components/intelligence/NotificationDrawer';
import { intelligenceApi } from '../services/intelligenceApi';
import { AlertsResponse } from '../types';

export const MainLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null);
  const [alertsLoading, setAlertsLoading] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [location.pathname]);

  const fetchAlerts = async () => {
    try {
      setAlertsLoading(true);
      const res = await intelligenceApi.getAlerts();
      setAlertsData(res);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setAlertsLoading(false);
    }
  };

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Customers', path: '/customers', icon: Users },
    { label: 'Contacts', path: '/contacts', icon: UserCheck },
    { label: 'Products', path: '/products', icon: Package },
    { label: 'Quotations', path: '/quotations', icon: FileText },
    { label: 'Governance', path: '/governance', icon: ShieldCheck },
    { label: 'Inventory', path: '/inventory', icon: Warehouse },
    { label: 'Invoices', path: '/invoices', icon: CreditCard },
    { label: 'Subscriptions', path: '/subscriptions', icon: Repeat },
    { label: 'Deals Pipeline', path: '/deals', icon: TrendingUp },
    { label: 'Forecast', path: '/forecast', icon: BarChart3 },
    { label: 'Activities', path: '/activities', icon: Clock },
    { label: 'Automations', path: '/automations', icon: Workflow },
    { label: 'AI Intelligence', path: '/ai', icon: Sparkles },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getPageTitle = () => {
    const current = navItems.find(
      (item) => location.pathname === item.path || (item.path !== '/dashboard' && location.pathname.startsWith(item.path))
    );
    return current ? current.label : 'Command Center';
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white bg-grid-pattern relative">
      {/* Neo Glass Ambient Light Effects */}
      <div className="fixed top-0 left-1/4 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none animate-pulse-glow" />
      <div className="fixed bottom-0 right-1/4 w-[600px] h-[600px] bg-sky-600/10 rounded-full blur-[140px] pointer-events-none" />

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 bg-slate-900/80 backdrop-blur-glass-lg border-r border-slate-800 flex-col justify-between p-4 z-20 shadow-2xl">
        <div>
          {/* Logo Header */}
          <div className="flex items-center gap-3 px-2 py-4 mb-6 border-b border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 border border-indigo-400/40 flex items-center justify-center font-black text-white text-xl shadow-neo">
              DF
            </div>
            <div>
              <h1 className="font-black text-slate-100 tracking-tight text-base leading-none">DealFlow360</h1>
              <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase tracking-widest">Neo Glass CRM</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col gap-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.path || (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-extrabold transition-all duration-150 group ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-neo border border-indigo-400/40'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  {/* Left Active Indicator */}
                  {isActive && <div className="absolute -left-4 top-2 bottom-2 w-1.5 bg-indigo-400 rounded-r-md" />}
                  <Icon className={`w-4 h-4 shrink-0 ${item.path === '/ai' ? 'text-purple-400' : ''}`} />
                  <span className="flex-1">{item.label}</span>
                  {isActive && <ChevronRight className="w-3.5 h-3.5 opacity-80" />}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Footer Card */}
        <div className="pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
            <div className="flex flex-col min-w-0 pr-2">
              <span className="font-extrabold text-slate-200 truncate">{user?.full_name || user?.email || 'User'}</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold">
                  {user?.is_admin ? 'Admin Role' : 'User Role'}
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              aria-label="Sign out"
              className="p-2 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden z-10">
        {/* Topbar */}
        <header className="h-16 bg-slate-900/60 backdrop-blur-glass border-b border-slate-800 px-6 flex items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
              className="md:hidden p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div>
              <h2 className="text-base font-black text-slate-100 tracking-tight">{getPageTitle()}</h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Alerts Notification Bell */}
            <button
              onClick={() => setAlertsOpen(true)}
              aria-label="Alerts"
              className="relative p-2 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-slate-300 hover:text-slate-100 transition shadow-neo"
            >
              <Bell className="w-4 h-4" />
              {alertsData && alertsData.unread_count > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 text-white font-mono text-[9px] font-extrabold flex items-center justify-center rounded-full border border-slate-950 animate-pulse">
                  {alertsData.unread_count}
                </span>
              )}
            </button>

            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs font-mono text-slate-300">
              <Building2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Tenant: {user?.organization_id?.substring(0, 8) || 'Active'}</span>
            </div>

            <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-400/40 flex items-center justify-center font-bold text-xs text-indigo-300">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      {/* Notification Drawer */}
      <NotificationDrawer
        isOpen={alertsOpen}
        onClose={() => setAlertsOpen(false)}
        alertsData={alertsData}
        isLoading={alertsLoading}
      />

      {/* Mobile Drawer Navigation */}
      <GlassDrawer isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} title="DealFlow360 Navigation">
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-neo border border-indigo-400/40'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold text-rose-400 hover:bg-rose-500/10 mt-6 border border-rose-500/30"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </nav>
      </GlassDrawer>
    </div>
  );
};

