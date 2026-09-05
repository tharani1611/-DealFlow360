export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  organization_id: string;
  is_active: boolean;
  is_admin: boolean;
  role: 'admin' | 'user';
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface Customer {
  id: string;
  organization_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  name: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  is_active?: boolean;
}

export interface CustomerUpdate {
  name?: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  is_active?: boolean;
}

export interface Contact {
  id: string;
  organization_id: string;
  customer_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  job_title: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContactCreate {
  customer_id: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  job_title?: string | null;
  is_primary?: boolean;
}

export interface ContactUpdate {
  first_name?: string;
  last_name?: string;
  email?: string | null;
  phone?: string | null;
  job_title?: string | null;
  is_primary?: boolean;
}

export interface Product {
  id: string;
  organization_id: string;
  name: string;
  sku: string;
  description: string | null;
  unit_price: string;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  sku: string;
  description?: string | null;
  unit_price: number | string;
  currency?: string;
  is_active?: boolean;
}

export interface ProductUpdate {
  name?: string;
  sku?: string;
  description?: string | null;
  unit_price?: number | string;
  currency?: string;
  is_active?: boolean;
}

export interface QuotationItem {
  id: string;
  quotation_id: string;
  product_id: string;
  product_variant_id?: string | null;
  product_name: string;
  sku?: string | null;
  description?: string | null;
  sequence?: number;
  quantity: number;
  unit_price: string;
  discount_percent?: string | number;
  discount_amount?: string | number;
  tax_rate?: string | number;
  tax_amount?: string | number;
  line_total: string;
  created_at?: string;
  updated_at?: string;
}

export interface QuotationItemCreate {
  product_id: string;
  product_variant_id?: string | null;
  description?: string | null;
  quantity: number;
  unit_price?: number | string;
  discount_percent?: number | string;
  discount_amount?: number | string;
  tax_rate?: number | string;
  tax_amount?: number | string;
  sequence?: number;
}

export type QuotationStatus = 'draft' | 'priced' | 'sent' | 'accepted' | 'rejected' | 'expired' | 'cancelled' | 'converted';

export interface QuotationStateHistoryItem {
  id: string;
  organization_id: string;
  quotation_id: string;
  from_status?: string | null;
  to_status: string;
  changed_by_user_id?: string | null;
  changed_by_user_name?: string | null;
  reason?: string | null;
  created_at: string;
}

export interface QuotationTransitionRequest {
  target_status: QuotationStatus;
  reason?: string;
}

export interface Quotation {
  id: string;
  organization_id: string;
  customer_id: string;
  contact_id?: string | null;
  deal_id?: string | null;
  title?: string | null;
  quotation_number: string;
  status: QuotationStatus;
  currency?: string;
  quotation_date: string;
  valid_until: string | null;
  notes: string | null;
  terms?: string | null;
  created_by_user_id?: string | null;
  updated_by_user_id?: string | null;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  created_at: string;
  updated_at: string;
  items?: QuotationItem[];
  customer?: Customer;
}

export interface QuotationCreate {
  customer_id: string;
  contact_id?: string | null;
  deal_id?: string | null;
  title?: string | null;
  currency?: string;
  quotation_date?: string;
  valid_until?: string | null;
  notes?: string | null;
  terms?: string | null;
  discount_amount?: number | string;
  tax_amount?: number | string;
  items: QuotationItemCreate[];
}

export interface QuotationUpdate {
  customer_id?: string;
  contact_id?: string | null;
  deal_id?: string | null;
  title?: string | null;
  currency?: string;
  valid_until?: string | null;
  notes?: string | null;
  terms?: string | null;
  discount_amount?: number | string;
  tax_amount?: number | string;
  items?: QuotationItemCreate[];
}

export type DealStage = 'new' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost';
export type DealStatus = 'open' | 'won' | 'lost';

export interface Deal {
  id: string;
  organization_id: string;
  customer_id: string;
  contact_id: string | null;
  quotation_id: string | null;
  title: string;
  description: string | null;
  deal_number: string;
  stage: DealStage;
  status: DealStatus;
  value: string;
  probability: number;
  expected_close_date: string | null;
  lost_reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  customer?: Customer;
  contact?: Contact;
  quotation?: Quotation;
}

export interface DealCreate {
  customer_id: string;
  title: string;
  description?: string | null;
  contact_id?: string | null;
  quotation_id?: string | null;
  stage?: DealStage;
  value?: number | string;
  probability?: number;
  expected_close_date?: string | null;
  notes?: string | null;
}

export interface DealUpdate {
  title?: string;
  description?: string | null;
  customer_id?: string;
  contact_id?: string | null;
  quotation_id?: string | null;
  stage?: DealStage;
  value?: number | string;
  probability?: number;
  expected_close_date?: string | null;
  notes?: string | null;
  lost_reason?: string | null;
}

export type ActivityType = 'task' | 'call' | 'meeting' | 'email' | 'note' | 'follow_up';
export type ActivityStatus = 'pending' | 'completed' | 'cancelled';
export type ActivityPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Activity {
  id: string;
  organization_id: string;
  activity_type: ActivityType;
  title: string;
  description: string | null;
  status: ActivityStatus;
  priority: ActivityPriority;
  customer_id: string | null;
  contact_id: string | null;
  deal_id: string | null;
  quotation_id: string | null;
  assigned_to_user_id: string | null;
  created_by_user_id: string;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  customer?: Customer;
  contact?: Contact;
  deal?: Deal;
}

export interface ActivityCreate {
  activity_type: ActivityType;
  title: string;
  description?: string | null;
  priority?: ActivityPriority;
  customer_id?: string | null;
  contact_id?: string | null;
  deal_id?: string | null;
  quotation_id?: string | null;
  assigned_to_user_id?: string | null;
  due_at?: string | null;
}

export interface ActivityUpdate {
  title?: string;
  description?: string | null;
  activity_type?: ActivityType;
  priority?: ActivityPriority;
  due_at?: string | null;
  assigned_to_user_id?: string | null;
}

export interface AIMetadata {
  provider: string;
  model: string;
  generated_at: string;
}

export interface CustomerSummaryResponse {
  customer_id: string;
  customer_name: string;
  summary: string;
  key_insights: string[];
  health_score_estimate: 'good' | 'neutral' | 'at_risk';
  metadata: AIMetadata;
}

export interface DealAnalysisResponse {
  deal_id: string;
  deal_number: string;
  summary: string;
  risk_level: 'low' | 'medium' | 'high';
  risks: string[];
  positive_signals: string[];
  recommended_actions: string[];
  metadata: AIMetadata;
}

export interface NextActionResponse {
  deal_id: string;
  action_type: ActivityType;
  title: string;
  reason: string;
  priority: ActivityPriority;
  metadata: AIMetadata;
}

export interface ActivityInsightResponse {
  deal_id: string;
  summary: string;
  overdue_count: number;
  upcoming_count: number;
  insights: string[];
  recommended_follow_ups: string[];
  metadata: AIMetadata;
}

export interface AssistantResponse {
  answer: string;
  context_used_count: number;
  referenced_deal_ids: string[];
  metadata: AIMetadata;
}

export interface RiskFactor {
  code: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  recommendation: string;
}

export interface DealHealthMetrics {
  probability: number;
  overdue_activity_count: number;
  days_until_expected_close?: number | null;
  recent_activity_count: number;
  has_accepted_quotation: boolean;
  has_expired_or_rejected_quotation: boolean;
}

export interface DealHealthResponse {
  deal_id: string;
  deal_number: string;
  title: string;
  health_score: number;
  health_status: 'healthy' | 'stable' | 'at_risk' | 'critical';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: RiskFactor[];
  metrics: DealHealthMetrics;
  ai_explanation?: string | null;
  metadata?: AIMetadata | null;
}

export interface CustomerEngagementMetrics {
  last_activity_at?: string | null;
  recent_activity_count_30d: number;
  overdue_activity_count: number;
  open_deal_count: number;
  total_open_deal_value: string;
  accepted_quotation_count: number;
}

export interface CustomerEngagementResponse {
  customer_id: string;
  customer_name: string;
  engagement_score: number;
  engagement_status: 'highly_engaged' | 'engaged' | 'cooling' | 'cold';
  is_going_cold: boolean;
  metrics: CustomerEngagementMetrics;
  risk_reasons: string[];
  ai_explanation?: string | null;
  metadata?: AIMetadata | null;
}

export interface SalesBriefingResponse {
  customer_id: string;
  customer_name: string;
  primary_contact_name?: string | null;
  primary_contact_email?: string | null;
  relationship_status: string;
  engagement_score: number;
  open_pipeline_value: string;
  active_deals_count: number;
  overdue_activities_count: number;
  deal_health_summary: Array<{
    deal_id: string;
    deal_number: string;
    title: string;
    stage: string;
    value: string;
    health_score: number;
    health_status: string;
  }>;
  attention_items: string[];
  talking_points: string[];
  suggested_next_actions: Array<{
    title: string;
    action_type: ActivityType;
    priority: ActivityPriority;
  }>;
  suggested_followup_message?: string | null;
  metadata?: AIMetadata | null;
}

export interface StageDistributionItem {
  stage: string;
  count: number;
  total_value: string;
  weighted_value: string;
}

export interface PipelineConcentration {
  top_deals_value_ratio: number;
  is_concentrated: boolean;
  top_deals_count: number;
  recommendation: string;
}

export interface PipelineMetrics {
  open_pipeline_value: string;
  weighted_pipeline_value: string;
  won_pipeline_value: string;
  lost_pipeline_value: string;
  at_risk_pipeline_value: string;
  win_rate?: string;
  average_deal_value?: string;
  forecast_confidence_label: string;
  concentration?: PipelineConcentration;
  stage_breakdown?: StageDistributionItem[];
}

export interface DashboardIntelligenceResponse {
  pipeline: PipelineMetrics;
  deal_health_counts: Record<string, number>;
  deals_at_risk: DealHealthResponse[];
  customers_going_cold: CustomerEngagementResponse[];
  needs_attention_count: number;
}

export interface AttentionItem {
  id: string;
  type: 'activity_overdue' | 'deal_risk' | 'customer_cooling' | 'deal_closing' | 'quotation_pending' | 'deal_stalled';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  entity_type: 'deal' | 'customer' | 'quotation' | 'activity';
  entity_id: string;
  action_label: string;
}

export interface AttentionCenterResponse {
  items: AttentionItem[];
  critical_count: number;
  high_count: number;
  total_count: number;
}

export interface AlertNotification {
  id: string;
  type: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  entity_type?: string | null;
  entity_id?: string | null;
  created_at: string;
}

export interface AlertsResponse {
  alerts: AlertNotification[];
  unread_count: number;
  generated_at: string;
}

export interface ActivityProductivityMetrics {
  today_count: number;
  upcoming_7d_count: number;
  overdue_count: number;
  completed_this_week_count: number;
}

export interface ProductRecommendationRule {
  id: string;
  organization_id: string;
  source_product_id: string;
  target_product_id: string;
  rule_type: 'upsell' | 'cross_sell';
  priority: number;
  is_active: boolean;
  min_customer_deal_count?: number | null;
  min_customer_pipeline_value?: string | null;
  min_customer_activity_count?: number | null;
  description?: string | null;
  created_at: string;
  updated_at: string;
  source_product_name?: string | null;
  source_product_sku?: string | null;
  target_product_name?: string | null;
  target_product_sku?: string | null;
}

export interface ProductRecommendationRuleCreate {
  source_product_id: string;
  target_product_id: string;
  rule_type: 'upsell' | 'cross_sell';
  priority?: number;
  is_active?: boolean;
  min_customer_deal_count?: number | null;
  min_customer_pipeline_value?: number | string | null;
  min_customer_activity_count?: number | null;
  description?: string | null;
}

export interface ProductRecommendationItem {
  product_id: string;
  product_name: string;
  sku: string;
  unit_price: string;
  recommendation_type: 'upsell' | 'cross_sell';
  source_product_id: string;
  source_product_name: string;
  priority: number;
  eligibility: string;
  reason: string;
  rule_id: string;
}

export interface CustomerProductRecommendationsResponse {
  customer_id: string;
  customer_name: string;
  recommendations: ProductRecommendationItem[];
}

export type ForecastCategory = 'COMMITTED' | 'UPSIDE' | 'PIPELINE' | 'AT_RISK';
export type ConfidenceLabel = 'HIGH CONFIDENCE' | 'MODERATE CONFIDENCE' | 'LOW CONFIDENCE' | 'VERY LOW CONFIDENCE';

export interface DealForecastItem {
  deal_id: string;
  deal_number: string;
  title: string;
  customer_id: string;
  customer_name: string;
  value: string;
  stage: string;
  base_probability: number;
  adjusted_probability: number;
  forecast_category: ForecastCategory;
  health_score: number;
  health_status: string;
  risk_count: number;
  expected_close_date?: string | null;
  weighted_value: string;
  forecast_value: string;
  primary_positive_factor?: string | null;
  primary_negative_factor?: string | null;
  positive_factors: string[];
  negative_factors: string[];
}

export interface PeriodForecast {
  period_key: string;
  period_label: string;
  open_pipeline: string;
  weighted_pipeline: string;
  forecast_revenue: string;
  committed_revenue: string;
  upside_revenue: string;
  at_risk_revenue: string;
  deal_count: number;
}

export interface ForecastConfidenceFactors {
  positive_factors: string[];
  negative_factors: string[];
}

export interface RevenueForecastResponse {
  open_pipeline: string;
  weighted_pipeline: string;
  forecast_revenue: string;
  committed_revenue: string;
  upside_revenue: string;
  at_risk_revenue: string;
  won_revenue: string;
  lost_revenue: string;
  confidence_score: number;
  confidence_label: ConfidenceLabel;
  concentration_risk: boolean;
  periods: PeriodForecast[];
  deals: DealForecastItem[];
  confidence_factors: ForecastConfidenceFactors;
}

export interface PricingRule {
  id: string;
  organization_id: string;
  name: string;
  rule_type: 'contract' | 'customer' | 'volume' | 'promotion';
  product_id: string;
  customer_id?: string | null;
  min_quantity: number | string;
  max_quantity?: number | string | null;
  price_type: 'override_price' | 'percentage_discount' | 'fixed_discount';
  value: number | string;
  priority: number;
  valid_from?: string | null;
  valid_until?: string | null;
  is_active: boolean;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PricingCalculateRequest {
  product_id: string;
  quantity: number | string;
  customer_id?: string | null;
  quotation_date?: string;
  currency?: string;
  manual_unit_price?: number | string | null;
}

export interface PricingCalculateResponse {
  base_price: string;
  selected_unit_price: string;
  final_unit_price: string;
  quantity: string;
  currency: string;
  pricing_source: 'BASE_PRODUCT_PRICE' | 'CONTRACT' | 'CUSTOMER' | 'VOLUME' | 'PROMOTION' | 'MANUAL_OVERRIDE';
  applied_rule_id?: string | null;
  applied_rule_name?: string | null;
  discount_amount: string;
  discount_percent: string;
  explanation: string;
}

export type MarginHealthStatus = 'HEALTHY' | 'CAUTION' | 'AT_RISK' | 'NEGATIVE';

export interface LineMarginResponse {
  product_id: string;
  product_name: string;
  quantity: string;
  unit_selling_price: string;
  unit_cost: string;
  line_revenue: string;
  line_cost: string;
  gross_margin: string;
  margin_percent: string;
  health_status: MarginHealthStatus;
  pricing_source: string;
  explanation: string;
}

export interface QuotationMarginResponse {
  quotation_id?: string | null;
  quotation_number?: string | null;
  customer_id?: string | null;
  currency: string;
  total_revenue: string;
  total_cost: string;
  gross_margin: string;
  margin_percent: string;
  health_status: MarginHealthStatus;
  items: LineMarginResponse[];
  explanation: string;
}

export interface DiscountPolicy {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  priority: number;
  scope: 'user' | 'customer' | 'product' | 'role' | 'organization';
  product_id?: string | null;
  customer_id?: string | null;
  user_id?: string | null;
  role?: string | null;
  max_discount_percent?: string | number | null;
  max_discount_amount?: string | number | null;
  minimum_unit_price?: string | number | null;
  minimum_margin_percent?: string | number | null;
  valid_from?: string | null;
  valid_until?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DiscountPolicyCreate {
  name: string;
  description?: string | null;
  is_active?: boolean;
  priority?: number;
  scope?: string;
  product_id?: string | null;
  customer_id?: string | null;
  user_id?: string | null;
  role?: string | null;
  max_discount_percent?: number | string | null;
  max_discount_amount?: number | string | null;
  minimum_unit_price?: number | string | null;
  minimum_margin_percent?: number | string | null;
  valid_from?: string | null;
  valid_until?: string | null;
}

export interface GovernanceViolation {
  rule_id?: string | null;
  rule_name?: string | null;
  violation_type: string;
  message: string;
  product_id?: string | null;
  product_name?: string | null;
  requested_val: string;
  policy_limit_val: string;
}

export interface GovernanceEvaluationResult {
  compliant: boolean;
  status: 'WITHIN_POLICY' | 'OUTSIDE_POLICY' | 'NO_POLICY';
  blended_discount_percent: string | number;
  applied_policies_count: number;
  violations: GovernanceViolation[];
  explanation: string;
}

export interface DiscountRiskFactor {
  code: string;
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score_impact: number;
}

export interface RiskEvaluationResult {
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  blended_discount_percent: string | number;
  overall_margin_percent: string | number;
  has_negative_margin: boolean;
  has_manual_override: boolean;
  has_policy_violation: boolean;
  risk_factors: DiscountRiskFactor[];
  explanation: string;
}

export interface ApprovalRule {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  priority: number;
  min_discount_percent?: string | number | null;
  max_discount_percent?: string | number | null;
  min_margin_percent?: string | number | null;
  risk_level?: string | null;
  quotation_value_threshold?: string | number | null;
  approval_level: number;
  required_role: string;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRuleCreate {
  name: string;
  description?: string | null;
  is_active?: boolean;
  priority?: number;
  min_discount_percent?: number | string | null;
  max_discount_percent?: number | string | null;
  min_margin_percent?: number | string | null;
  risk_level?: string | null;
  quotation_value_threshold?: number | string | null;
  approval_level?: number;
  required_role?: string;
}

export interface QuotationApproval {
  id: string;
  organization_id: string;
  quotation_id: string;
  approval_rule_id?: string | null;
  requested_by_user_id: string;
  requested_by_user_name?: string | null;
  approved_by_user_id?: string | null;
  approved_by_user_name?: string | null;
  status: 'NOT_REQUIRED' | 'PENDING' | 'APPROVED' | 'REJECTED' | 'INVALIDATED';
  approval_level: number;
  reasons?: string | null;
  decision_note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApprovalDecisionRequest {
  decision: 'APPROVED' | 'REJECTED';
  note?: string;
}

export interface CommercialGovernanceSummaryResponse {
  quotation_id?: string | null;
  quotation_number?: string | null;
  customer_id?: string | null;
  currency: string;
  total_amount: string;
  margin: QuotationMarginResponse;
  governance: GovernanceEvaluationResult;
  risk: RiskEvaluationResult;
  approval: QuotationApproval;
}

export type CopilotIntentType =
  | 'PIPELINE'
  | 'DEAL'
  | 'CUSTOMER'
  | 'QUOTATION'
  | 'PRICING'
  | 'MARGIN'
  | 'DISCOUNT'
  | 'APPROVAL'
  | 'ACTIVITY'
  | 'GENERAL_SALES';

export interface CopilotEvidenceItem {
  entity_type: string;
  entity_id?: string | null;
  label: string;
  value: string;
  detail?: string | null;
}

export interface CopilotRequest {
  message: string;
  deal_id?: string | null;
  customer_id?: string | null;
  quotation_id?: string | null;
}

export interface CopilotResponse {
  answer: string;
  intent: CopilotIntentType;
  evidence: CopilotEvidenceItem[];
  recommendations: string[];
  referenced_deal_ids: string[];
  referenced_customer_ids: string[];
  referenced_quotation_ids: string[];
  metadata: AIMetadata;
}

export interface DealQARequest {
  question: string;
}

export interface DealQAResponse {
  deal_id: string;
  question: string;
  answer: string;
  key_facts: string[];
  recommended_action?: string | null;
  metadata: AIMetadata;
}

