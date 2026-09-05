import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { customerApi } from '../services/customerApi';
import { Customer } from '../types';
import { DataTable, Column } from '../components/ui/DataTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassModal } from '../components/ui/GlassModal';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { Plus, Search, ExternalLink } from 'lucide-react';

export const CustomersPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [city, setCity] = useState('');

  const loadCustomers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await customerApi.getCustomers({ search: searchTerm.trim() || undefined });
      setCustomers(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch customer directory.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, [searchTerm]);

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSaving(true);
    try {
      await customerApi.createCustomer({
        name: name.trim(),
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        city: city.trim() || undefined,
      });
      showToast(`Customer "${name}" created successfully!`, 'success');
      setIsModalOpen(false);
      setName('');
      setEmail('');
      setPhone('');
      setCity('');
      loadCustomers();
    } catch (err: any) {
      showToast(err.message || 'Failed to create customer record.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const columns: Column<Customer>[] = [
    {
      header: 'Customer Name',
      render: (row) => (
        <div>
          <span className="font-extrabold text-slate-100 text-sm">{row.name}</span>
          <span className="text-[10px] font-mono text-slate-500 block">ID: {row.id.substring(0, 8)}...</span>
        </div>
      ),
    },
    {
      header: 'Contact Info',
      render: (row) => (
        <div className="text-xs">
          <div className="text-slate-200">{row.email || '—'}</div>
          <div className="text-slate-400 text-[11px]">{row.phone || '—'}</div>
        </div>
      ),
    },
    {
      header: 'Location',
      render: (row) => (
        <span className="text-xs text-slate-300 font-mono">
          {[row.city, row.country].filter(Boolean).join(', ') || '—'}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (row) => <StatusBadge status={row.is_active ? 'active' : 'inactive'} size="sm" />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <BrutalButton
          size="sm"
          variant="ghost"
          icon={ExternalLink}
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/customers/${row.id}`);
          }}
        >
          View Details
        </BrutalButton>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Customer Directory</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Manage organization accounts, contacts, and historical relationship telemetry
          </p>
        </div>

        <BrutalButton variant="primary" icon={Plus} onClick={() => setIsModalOpen(true)}>
          New Customer Account
        </BrutalButton>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex items-center gap-3 bg-slate-900/60 backdrop-blur-glass border border-slate-800 rounded-xl p-3 shadow-neo-sm">
        <Search className="w-4 h-4 text-slate-400 shrink-0 ml-2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by customer name..."
          className="w-full bg-transparent border-none text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none"
        />
      </div>

      {/* Table Section */}
      {isLoading ? (
        <LoadingState message="Fetching customer records..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadCustomers} />
      ) : (
        <DataTable
          columns={columns}
          data={customers}
          keyExtractor={(row) => row.id}
          emptyMessage="No customer accounts match your criteria."
          onRowClick={(row) => navigate(`/customers/${row.id}`)}
        />
      )}

      {/* Create Modal */}
      <GlassModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Customer Account"
        subtitle="Add a new customer organization to DealFlow360"
      >
        <form onSubmit={handleCreateCustomer} className="space-y-4">
          <GlassInput
            label="Customer / Account Name"
            placeholder="e.g. Enterprise Global Systems"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <GlassInput
            label="Primary Email Address"
            type="email"
            placeholder="contact@enterprise.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <GlassInput
            label="Phone Number"
            placeholder="+1 (555) 019-2834"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <GlassInput
            label="City / Location"
            placeholder="e.g. San Francisco, CA"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSaving}>
              Save Customer Account
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
