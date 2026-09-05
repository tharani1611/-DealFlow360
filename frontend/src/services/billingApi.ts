import { fetchApi } from './apiClient';
import {
  Invoice,
  InvoiceCreate,
  Payment,
  PaymentCreate,
  Subscription,
  SubscriptionCreate,
  BillingSchedule,
  ProrationCalculation,
  SubscriptionProration,
  SubscriptionCancellation,
  CreditNote,
  CreditNoteCreate,
  PaymentRefund,
} from '../types';

export const billingApi = {
  // Invoices
  listInvoices: (customerId?: string) => {
    const query = customerId ? `?customer_id=${customerId}` : '';
    return fetchApi<Invoice[]>(`/invoices${query}`);
  },

  getInvoice: (id: string) => {
    return fetchApi<Invoice>(`/invoices/${id}`);
  },

  createInvoice: (payload: InvoiceCreate) => {
    return fetchApi<Invoice>('/invoices', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  createInvoiceFromQuotation: (quotationId: string) => {
    return fetchApi<Invoice>(`/invoices/from-quotation/${quotationId}`, {
      method: 'POST',
    });
  },

  issueInvoice: (id: string) => {
    return fetchApi<Invoice>(`/invoices/${id}/issue`, {
      method: 'POST',
    });
  },

  voidInvoice: (id: string) => {
    return fetchApi<Invoice>(`/invoices/${id}/void`, {
      method: 'POST',
    });
  },

  // Payments
  recordPayment: (payload: PaymentCreate) => {
    return fetchApi<Payment>('/payments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listPaymentsForInvoice: (invoiceId: string) => {
    return fetchApi<Payment[]>(`/payments/invoice/${invoiceId}`);
  },

  // Subscriptions
  listSubscriptions: (customerId?: string) => {
    const query = customerId ? `?customer_id=${customerId}` : '';
    return fetchApi<Subscription[]>(`/subscriptions${query}`);
  },

  getSubscription: (id: string) => {
    return fetchApi<Subscription>(`/subscriptions/${id}`);
  },

  createSubscription: (payload: SubscriptionCreate) => {
    return fetchApi<Subscription>('/subscriptions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  createSubscriptionsFromQuotation: (quotationId: string) => {
    return fetchApi<Subscription[]>(`/subscriptions/from-quotation/${quotationId}`, {
      method: 'POST',
    });
  },

  updateSubscriptionStatus: (id: string, status: string) => {
    return fetchApi<Subscription>(`/subscriptions/${id}/status?new_status=${status}`, {
      method: 'PUT',
    });
  },

  listSchedulesForSubscription: (subscriptionId: string) => {
    return fetchApi<BillingSchedule[]>(`/subscriptions/${subscriptionId}/schedules`);
  },

  generateDueSchedules: (asOfDate?: string) => {
    const query = asOfDate ? `?as_of_date=${asOfDate}` : '';
    return fetchApi<BillingSchedule[]>(`/subscriptions/schedules/generate-due${query}`, {
      method: 'POST',
    });
  },

  executeScheduleInvoice: (scheduleId: string) => {
    return fetchApi<Invoice>(`/subscriptions/schedules/${scheduleId}/execute-invoice`, {
      method: 'POST',
    });
  },

  calculateProration: (id: string, payload: { new_quantity: number; new_unit_price: number | string; effective_date?: string }) => {
    return fetchApi<ProrationCalculation>(`/subscriptions/${id}/proration/calculate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  applyProration: (id: string, payload: { new_quantity: number; new_unit_price: number | string; effective_date?: string; notes?: string }) => {
    return fetchApi<SubscriptionProration>(`/subscriptions/${id}/proration/apply`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  cancelSubscription: (id: string, payload: { cancellation_type: 'IMMEDIATE' | 'END_OF_PERIOD'; reason: string; effective_date?: string; notes?: string }) => {
    return fetchApi<SubscriptionCancellation>(`/subscriptions/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Credit Notes & Refunds
  createCreditNote: (payload: CreditNoteCreate) => {
    return fetchApi<CreditNote>('/credit-notes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getCreditNote: (id: string) => {
    return fetchApi<CreditNote>(`/credit-notes/${id}`);
  },

  listCreditNotesForInvoice: (invoiceId: string) => {
    return fetchApi<CreditNote[]>(`/credit-notes/invoice/${invoiceId}`);
  },

  createPaymentRefund: (payload: { payment_id: string; credit_note_id?: string; amount: number | string; reason: string; refund_date?: string }) => {
    return fetchApi<PaymentRefund>('/credit-notes/refunds', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listRefundsForPayment: (paymentId: string) => {
    return fetchApi<PaymentRefund[]>(`/credit-notes/refunds/payment/${paymentId}`);
  },
};
