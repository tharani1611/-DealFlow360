import React, { useState, useEffect } from 'react';
import { contactApi } from '../services/contactApi';
import { customerApi } from '../services/customerApi';
import { Contact, Customer } from '../types';
import { DataTable, Column } from '../components/ui/DataTable';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassCheckbox } from '../components/ui/GlassCheckbox';
import { GlassModal } from '../components/ui/GlassModal';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { Plus } from 'lucide-react';

export const ContactsPage: React.FC = () => {
  const { showToast } = useToast();

  const [contacts, setContacts] = useState<Contact[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [isPrimary, setIsPrimary] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [contactsData, custData] = await Promise.all([
        contactApi.getContacts(),
        customerApi.getCustomers(),
      ]);
      setContacts(contactsData);
      setCustomers(custData);
      if (custData.length > 0 && !customerId) {
        setCustomerId(custData[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch contact directory.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim() || !customerId) return;

    setIsSaving(true);
    try {
      await contactApi.createContact({
        customer_id: customerId,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        job_title: jobTitle.trim() || undefined,
        is_primary: isPrimary,
      });
      showToast(`Contact "${firstName} ${lastName}" created successfully!`, 'success');
      setIsModalOpen(false);
      setFirstName('');
      setLastName('');
      setEmail('');
      setPhone('');
      setJobTitle('');
      setIsPrimary(false);
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to create contact.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const getCustomerName = (cust_id: string) => {
    const found = customers.find((c) => c.id === cust_id);
    return found ? found.name : cust_id.substring(0, 8);
  };

  const columns: Column<Contact>[] = [
    {
      header: 'Contact Name',
      render: (r) => (
        <div>
          <span className="font-extrabold text-slate-100 text-sm">{r.first_name} {r.last_name}</span>
          {r.is_primary && (
            <span className="ml-2 text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-500/40 px-1.5 py-0.5 rounded font-mono font-bold">
              PRIMARY
            </span>
          )}
        </div>
      ),
    },
    { header: 'Job Title', accessor: 'job_title' },
    {
      header: 'Customer Account',
      render: (r) => <span className="text-xs font-mono text-indigo-300">{getCustomerName(r.customer_id)}</span>,
    },
    { header: 'Email', accessor: 'email' },
    { header: 'Phone', accessor: 'phone' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Contact Directory</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Key customer decision makers and primary account contacts
          </p>
        </div>

        <BrutalButton variant="primary" icon={Plus} onClick={() => setIsModalOpen(true)}>
          New Contact
        </BrutalButton>
      </div>

      {isLoading ? (
        <LoadingState message="Loading contacts telemetry..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : (
        <DataTable
          columns={columns}
          data={contacts}
          keyExtractor={(r) => r.id}
          emptyMessage="No contacts available in the directory."
        />
      )}

      {/* Create Contact Modal */}
      <GlassModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Account Contact"
        subtitle="Add a key contact to a customer account"
      >
        <form onSubmit={handleCreateContact} className="space-y-4">
          <GlassSelect
            label="Customer Account"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            options={customers.map((c) => ({ value: c.id, label: c.name }))}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <GlassInput
              label="First Name"
              placeholder="e.g. John"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
            <GlassInput
              label="Last Name"
              placeholder="e.g. Smith"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>

          <GlassInput
            label="Job Title"
            placeholder="e.g. Vice President of Sales"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
          />

          <GlassInput
            label="Email Address"
            type="email"
            placeholder="john.smith@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <GlassInput
            label="Phone Number"
            placeholder="+1 (555) 019-2834"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />

          <GlassCheckbox
            label="Mark as Primary Contact for this Account"
            checked={isPrimary}
            onChange={(e) => setIsPrimary(e.target.checked)}
          />

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSaving}>
              Save Contact
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
