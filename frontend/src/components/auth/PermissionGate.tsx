import React from 'react';
import { usePermissions, Permissions } from '../../hooks/usePermissions';

interface PermissionGateProps {
  children: React.ReactNode;
  requires?: (permissions: Permissions) => boolean;
  adminOnly?: boolean;
  fallback?: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  children,
  requires,
  adminOnly,
  fallback = null,
}) => {
  const permissions = usePermissions();

  if (adminOnly && !permissions.isAdmin) {
    return <>{fallback}</>;
  }

  if (requires && !requires(permissions)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
