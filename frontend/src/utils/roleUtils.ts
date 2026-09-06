import { User } from '../types';

export type RolePersona = 'admin' | 'sales_rep' | 'inventory_manager' | 'billing_controller';

export const getUserRole = (user: User | null): RolePersona => {
  if (!user) return 'admin';

  const email = (user.email || '').toLowerCase();

  if (email.startsWith('sales_') || email.startsWith('ae') || email.includes('sales')) {
    return 'sales_rep';
  }
  if (email.startsWith('inventory') || email.includes('inventory.mgr') || email.includes('warehouse')) {
    return 'inventory_manager';
  }
  if (email.startsWith('billing') || email.includes('finance') || email.includes('controller') || email.includes('billing')) {
    return 'billing_controller';
  }
  if (user.is_admin || email.startsWith('admin') || email.includes('admin') || email.includes('owner')) {
    return 'admin';
  }

  return user.is_admin ? 'admin' : 'sales_rep';
};

export const getRoleLabel = (role: RolePersona): string => {
  switch (role) {
    case 'admin':
      return '👑 Admin / VP Sales';
    case 'sales_rep':
      return '💼 Sales Representative';
    case 'inventory_manager':
      return '📦 Inventory Manager';
    case 'billing_controller':
      return '💳 Billing Controller';
  }
};
