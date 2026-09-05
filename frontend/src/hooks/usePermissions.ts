import { useAuth } from '../context/AuthContext';

export interface Permissions {
  isAdmin: boolean;
  canApproveQuotations: boolean;
  canOverrideFulfillment: boolean;
  canProcessRefunds: boolean;
  canManageSettings: boolean;
  canManageUsers: boolean;
  canViewCostsAndMargins: boolean;
}

export const usePermissions = (): Permissions => {
  const { user } = useAuth();
  const isAdmin = user?.is_admin || user?.role === 'admin' || false;

  return {
    isAdmin,
    canApproveQuotations: isAdmin,
    canOverrideFulfillment: isAdmin,
    canProcessRefunds: isAdmin,
    canManageSettings: isAdmin,
    canManageUsers: isAdmin,
    canViewCostsAndMargins: isAdmin,
  };
};
