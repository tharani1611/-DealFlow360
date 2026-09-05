import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from '../layouts/MainLayout';

import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { CustomersPage } from '../pages/CustomersPage';
import { CustomerDetailPage } from '../pages/CustomerDetailPage';
import { ContactsPage } from '../pages/ContactsPage';
import { ProductsPage } from '../pages/ProductsPage';
import { QuotationsPage } from '../pages/QuotationsPage';
import { QuotationDetailPage } from '../pages/QuotationDetailPage';
import { DealsPage } from '../pages/DealsPage';
import { DealDetailPage } from '../pages/DealDetailPage';
import { ActivitiesPage } from '../pages/ActivitiesPage';
import { AIPage } from '../pages/AIPage';
import { SettingsPage } from '../pages/SettingsPage';
import { ForecastPage } from '../pages/ForecastPage';
import { LoadingState } from '../components/ui/EmptyState';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <LoadingState message="Verifying session telemetry..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      {/* Protected App Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/:id" element={<CustomerDetailPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="quotations" element={<QuotationsPage />} />
        <Route path="quotations/:id" element={<QuotationDetailPage />} />
        <Route path="deals" element={<DealsPage />} />
        <Route path="deals/:id" element={<DealDetailPage />} />
        <Route path="activities" element={<ActivitiesPage />} />
        <Route path="forecast" element={<ForecastPage />} />
        <Route path="ai" element={<AIPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
