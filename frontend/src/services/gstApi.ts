import { fetchApi } from './apiClient';

export interface GSTLineItemInput {
  description?: string;
  hsn_sac_code?: string;
  quantity: number;
  unit_price: number;
  discount_amount?: number;
  line_subtotal?: number;
  gst_rate: number;
}

export interface GSTTaxCalculationRequest {
  seller_state: string;
  buyer_state: string;
  items: GSTLineItemInput[];
}

export interface GSTProcessedLineItem {
  item_index: number;
  product_name: string;
  hsn_sac_code: string;
  quantity: string;
  unit_price: string;
  taxable_value: string;
  gst_rate: string;
  cgst_rate: string;
  cgst_amount: string;
  sgst_rate: string;
  sgst_amount: string;
  igst_rate: string;
  igst_amount: string;
  total_line_tax: string;
  total_line_value: string;
}

export interface GSTTaxCalculationResponse {
  tax_type: string;
  is_intra_state: boolean;
  seller_state: string;
  seller_state_code: string;
  buyer_state: string;
  buyer_state_code: string;
  total_taxable_value: string;
  total_cgst_amount: string;
  total_sgst_amount: string;
  total_igst_amount: string;
  total_tax_amount: string;
  grand_total: string;
  items: GSTProcessedLineItem[];
}

export interface EWayBillPayloadRequest {
  transporter_id?: string;
  vehicle_no?: string;
  distance_km?: number;
  seller_state?: string;
}

export const gstApi = {
  calculateTax: async (payload: GSTTaxCalculationRequest): Promise<GSTTaxCalculationResponse> => {
    return fetchApi<GSTTaxCalculationResponse>('/gst/calculate-tax', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getEInvoicePayload: async (invoiceId: string): Promise<Record<string, any>> => {
    return fetchApi<Record<string, any>>(`/invoices/${invoiceId}/einvoice-payload`);
  },

  getEWayBillPayload: async (invoiceId: string, payload: EWayBillPayloadRequest): Promise<Record<string, any>> => {
    return fetchApi<Record<string, any>>(`/invoices/${invoiceId}/ewaybill-payload`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
