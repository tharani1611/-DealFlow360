import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassInput } from '../ui/GlassInput';
import { BrutalButton } from '../ui/BrutalButton';
import { customerApi } from '../../services/customerApi';
import { CustomerCreate, Customer } from '../../types';
import { useToast } from '../../context/ToastContext';

interface CreateCustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (customer: Customer) => void;
  customerToEdit?: Customer | null;
}

export const CreateCustomerModal: React.FC<CreateCustomerModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  customerToEdit,
}) => {
  const { showToast } = useToast();
  const [name, setName] = useState(customerToEdit?.name || '');
  const [email, setEmail] = useState(customerToEdit?.email || '');
  const [phone, setPhone] = useState(customerToEdit?.phone || '');
  const [address, setAddress] = useState(customerToEdit?.address || '');
  const [city, setCity] = useState(customerToEdit?.city || '');
  const [country, setCountry] = useState(customerToEdit?.country || '');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsLoading(true);
    try {
      if (customerToEdit) {
        const updated = await customerApi.updateCustomer(customerToEdit.id, {
          name: name.trim(),
          email: email.trim() || null,
          phone: phone.trim() || null,
          address: address.trim() || null,
          city: city.trim() || null,
          country: country.trim() || null,
        });
        showToast('Customer account updated successfully.', 'success');
        onSuccess(updated);
      } else {
        const payload: CustomerCreate = {
          name: name.trim(),
          email: email.trim() || null,
          phone: phone.trim() || null,
          address: address.trim() || null,
          city: city.trim() || null,
          country: country.trim() || null,
          is_active: true,
        };
        const created = await customerApi.createCustomer(payload);
        showToast('Customer account created successfully.', 'success');
        onSuccess(created);
      }
      onClose();
    } catch (err: any) {
      showToast(err.message || 'Failed to save customer account.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={customerToEdit ? 'Edit Customer Account' : 'Create New Customer Account'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <GlassInput
          label="Customer / Account Name"
          placeholder="e.g. Acme Corporation"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <GlassInput
            label="Primary Email"
            type="email"
            placeholder="contact@company.com"
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
          label="Billing Address"
          placeholder="123 Business Way, Suite 400"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <GlassInput
            label="City"
            placeholder="New York"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />
          <GlassInput
            label="Country"
            placeholder="United States"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          />
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <BrutalButton type="button" variant="secondary" onClick={onClose}>
            Cancel
          </BrutalButton>
          <BrutalButton type="submit" variant="primary" isLoading={isLoading}>
            {customerToEdit ? 'Save Changes' : 'Create Account'}
          </BrutalButton>
        </div>
      </form>
    </GlassModal>
  );
};
