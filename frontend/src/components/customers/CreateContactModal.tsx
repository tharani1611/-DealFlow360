import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassInput } from '../ui/GlassInput';
import { BrutalButton } from '../ui/BrutalButton';
import { contactApi } from '../../services/contactApi';
import { ContactCreate, Contact } from '../../types';
import { useToast } from '../../context/ToastContext';

interface CreateContactModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerId: string;
  onSuccess: (contact: Contact) => void;
}

export const CreateContactModal: React.FC<CreateContactModalProps> = ({
  isOpen,
  onClose,
  customerId,
  onSuccess,
}) => {
  const { showToast } = useToast();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [isPrimary, setIsPrimary] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim()) return;

    setIsLoading(true);
    try {
      const payload: ContactCreate = {
        customer_id: customerId,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        job_title: jobTitle.trim() || null,
        is_primary: isPrimary,
      };
      const created = await contactApi.createContact(payload);
      showToast('Contact created successfully.', 'success');
      onSuccess(created);
      onClose();
    } catch (err: any) {
      showToast(err.message || 'Failed to create contact.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title="Add Customer Contact">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <GlassInput
            label="First Name"
            placeholder="Jane"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
          />
          <GlassInput
            label="Last Name"
            placeholder="Doe"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <GlassInput
            label="Email Address"
            type="email"
            placeholder="jane@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <GlassInput
            label="Phone Number"
            placeholder="+1 (555) 000-0000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </div>

        <GlassInput
          label="Job Title / Role"
          placeholder="VP of Procurement"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
        />

        <div className="flex items-center gap-2 pt-2">
          <input
            type="checkbox"
            id="is_primary"
            checked={isPrimary}
            onChange={(e) => setIsPrimary(e.target.checked)}
            className="rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
          />
          <label htmlFor="is_primary" className="text-xs text-slate-300">
            Set as Primary Account Contact
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <BrutalButton type="button" variant="secondary" onClick={onClose}>
            Cancel
          </BrutalButton>
          <BrutalButton type="submit" variant="primary" isLoading={isLoading}>
            Add Contact
          </BrutalButton>
        </div>
      </form>
    </GlassModal>
  );
};
