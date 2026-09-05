import { fetchApi } from './apiClient';
import {
  ApprovalAuditLog,
  LineComment,
  LineCommentCreate,
  ChangeRequest,
  ChangeRequestReview,
  CounterDiscountApply,
  QuotationVersion,
  Quotation
} from '../types';

export const negotiationApi = {
  getAuditLogs: async (quotationId: string): Promise<ApprovalAuditLog[]> => {
    return fetchApi<ApprovalAuditLog[]>(`/quotations/${quotationId}/audit-logs`);
  },

  getLineComments: async (quotationId: string, quotationItemId?: string): Promise<LineComment[]> => {
    const query = quotationItemId ? `?quotation_item_id=${quotationItemId}` : '';
    return fetchApi<LineComment[]>(`/quotations/${quotationId}/comments${query}`);
  },

  createLineComment: async (quotationId: string, payload: LineCommentCreate): Promise<LineComment> => {
    return fetchApi<LineComment>(`/quotations/${quotationId}/comments`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getChangeRequests: async (quotationId: string): Promise<ChangeRequest[]> => {
    return fetchApi<ChangeRequest[]>(`/quotations/${quotationId}/change-requests`);
  },

  reviewChangeRequest: async (
    quotationId: string,
    changeRequestId: string,
    payload: ChangeRequestReview
  ): Promise<ChangeRequest> => {
    return fetchApi<ChangeRequest>(`/quotations/${quotationId}/change-requests/${changeRequestId}/review`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  applyCounterDiscount: async (quotationId: string, payload: CounterDiscountApply): Promise<Quotation> => {
    return fetchApi<Quotation>(`/quotations/${quotationId}/counter-discount`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getVersions: async (quotationId: string): Promise<QuotationVersion[]> => {
    return fetchApi<QuotationVersion[]>(`/quotations/${quotationId}/versions`);
  },
};
