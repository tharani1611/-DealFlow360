import { fetchApi } from './apiClient';
import { CopilotRequest, CopilotResponse, DealQARequest, DealQAResponse } from '../types';

export const copilotApi = {
  chat: async (payload: CopilotRequest): Promise<CopilotResponse> => {
    return fetchApi<CopilotResponse>('/copilot/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  askDealQuestion: async (dealId: string, payload: DealQARequest): Promise<DealQAResponse> => {
    return fetchApi<DealQAResponse>(`/copilot/deals/${dealId}/qa`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
