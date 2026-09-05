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

export interface ForecastScenarios {
  conservative_revenue: string;
  base_revenue: string;
  optimistic_revenue: string;
}

export interface ForecastExplanationResponse {
  summary: string;
  risk_highlights: string[];
  recommendations: string[];
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
  coverage_ratio: string;
  confidence_score: number;
  confidence_label: ConfidenceLabel;
  concentration_risk: boolean;
  scenarios: ForecastScenarios;
  periods: PeriodForecast[];
  deals: DealForecastItem[];
  confidence_factors: ForecastConfidenceFactors;
  ai_explanation?: string | null;
}

export type RuleStatus = 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'ARCHIVED';
export type ExecutionStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED' | 'SKIPPED' | 'CANCELLED';

export interface AutomationCondition {
  field: string;
  operator: string;
  value?: any;
}

export interface AutomationConditionGroup {
  logical_operator: 'AND' | 'OR';
  conditions: AutomationCondition[];
  groups?: AutomationConditionGroup[];
}

export interface AutomationAction {
  action_type: string;
  parameters: Record<string, any>;
}

export interface AutomationRule {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  status: RuleStatus;
  priority: number;
  trigger_type: string;
  conditions: AutomationConditionGroup;
  actions: AutomationAction[];
  created_by_user_id?: string | null;
  updated_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AutomationRuleCreate {
  name: string;
  description?: string;
  trigger_type: string;
  priority?: number;
  conditions: AutomationConditionGroup;
  actions: AutomationAction[];
}

export interface AutomationRuleUpdate {
  name?: string;
  description?: string;
  trigger_type?: string;
  priority?: number;
  status?: RuleStatus;
  conditions?: AutomationConditionGroup;
  actions?: AutomationAction[];
}

export interface AutomationExecutionAction {
  id: string;
  execution_id: string;
  action_type: string;
  status: 'SUCCESS' | 'FAILED' | 'SKIPPED';
  result_payload: Record<string, any>;
  error_message?: string | null;
  executed_at: string;
}

export interface AutomationExecution {
  id: string;
  organization_id: string;
  rule_id: string;
  rule_name?: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  status: ExecutionStatus;
  idempotency_key: string;
  conditions_matched: boolean;
  actions_total: number;
  actions_succeeded: number;
  actions_failed: number;
  error_message?: string | null;
  retry_count: number;
  trigger_context: Record<string, any>;
  started_at: string;
  completed_at?: string | null;
  actions: AutomationExecutionAction[];
}

export interface AutomationAnalyticsSummary {
  total_rules: number;
  active_rules: number;
  paused_rules: number;
  draft_rules: number;
  executions_today: number;
  successful_executions: number;
  failed_executions: number;
  skipped_executions: number;
  success_rate_percent: number;
}

export interface AIRuleRecommendation {
  rule_name: string;
  description: string;
  trigger_type: string;
  reason: string;
  recommended_conditions: AutomationConditionGroup;
  recommended_actions: AutomationAction[];
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

export interface CustomerFinancialMetrics {
  total_won_revenue: string;
  open_pipeline: string;
  weighted_pipeline: string;
  quotation_revenue: string;
  gross_margin: string;
  margin_percentage: number;
  average_deal_value: string;
}

export interface CustomerSalesMetrics {
  deal_count: number;
  won_deal_count: number;
  lost_deal_count: number;
  open_deal_count: number;
  win_rate_percent: number;
  average_sales_cycle_days: number;
}

export interface CustomerEngagementDetails {
  last_activity_date?: string | null;
  days_since_last_activity: number;
  recency_classification: 'VERY_RECENT' | 'RECENT' | 'AGING' | 'STALE' | 'INACTIVE';
  activities_last_7_days: number;
  activities_last_30_days: number;
  overdue_activities_count: number;
  completed_activities_count: number;
}

export interface CustomerHealthDetail {
  health_score: number;
  health_category: 'HEALTHY' | 'ENGAGED' | 'ATTENTION' | 'AT_RISK' | 'INACTIVE';
  positive_drivers: string[];
  negative_drivers: string[];
  segment: 'ENTERPRISE' | 'HIGH_VALUE' | 'GROWTH' | 'ACTIVE' | 'DEVELOPING' | 'AT_RISK' | 'INACTIVE';
  lifecycle_stage: 'NEW' | 'DEVELOPING' | 'ACTIVE' | 'GROWING' | 'MATURE' | 'AT_RISK' | 'INACTIVE';
  risk_signals: string[];
}

export interface CustomerTrends {
  revenue_trend: 'UP' | 'DOWN' | 'STABLE' | 'NEW';
  deal_trend: 'UP' | 'DOWN' | 'STABLE' | 'NEW';
  activity_trend: 'UP' | 'DOWN' | 'STABLE' | 'NEW';
  pipeline_trend: 'UP' | 'DOWN' | 'STABLE' | 'NEW';
  engagement_trend: 'UP' | 'DOWN' | 'STABLE' | 'NEW';
}

export interface Customer360Intelligence {
  customer_id: string;
  customer_name: string;
  industry?: string | null;
  financials: CustomerFinancialMetrics;
  sales: CustomerSalesMetrics;
  engagement: CustomerEngagementDetails;
  health: CustomerHealthDetail;
  trends: CustomerTrends;
  purchased_product_ids: string[];
  ai_explanation?: string | null;
  metadata?: AIMetadata | null;
}

export interface ProductPerformanceMetrics {
  units_quoted: number;
  units_won: number;
  total_revenue: string;
  gross_margin: string;
  margin_percentage: number;
  quotation_count: number;
  deal_count: number;
  won_deal_count: number;
  win_rate_percent: number;
  average_selling_price: string;
  customer_count: number;
  penetration_rate_percent: number;
  popularity_score: number;
  popularity_rank: number;
}

export interface ProductAffinityItem {
  target_product_id: string;
  target_product_name: string;
  target_sku: string;
  unit_price: string;
  co_purchase_count: number;
  attachment_rate_percent: number;
  affinity_score: number;
  relationship_type: 'CROSS_SELL' | 'UPSELL' | 'COMPLEMENTARY';
}

export interface Product360Intelligence {
  product_id: string;
  name: string;
  sku: string;
  unit_price: string;
  unit_cost: string;
  is_active: boolean;
  description?: string | null;
  performance: ProductPerformanceMetrics;
  affinities: ProductAffinityItem[];
  top_customer_segments: string[];
  ai_explanation?: string | null;
  metadata?: AIMetadata | null;
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

// --- Original Phases 26–35 (Approval, Customer Portal, Negotiation) ---

export interface PortalUserResponse {
  id: string;
  organization_id: string;
  customer_id: string;
  contact_id?: string | null;
  email: string;
  full_name: string;
  is_active: boolean;
  last_login_at?: string | null;
}

export interface PortalTokenResponse {
  access_token: string;
  token_type: string;
  portal_user: PortalUserResponse;
}

export interface PortalQuotationItemResponse {
  id: string;
  product_id: string;
  product_name?: string | null;
  sku?: string | null;
  quantity: number | string;
  unit_price: string;
  discount_percent: number | string;
  line_total: string;
  notes?: string | null;
}

export interface PortalQuotationDetailResponse {
  id: string;
  quotation_number: string;
  customer_id: string;
  customer_name?: string | null;
  status: string;
  issue_date?: string | null;
  expiration_date?: string | null;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  currency: string;
  notes?: string | null;
  items: PortalQuotationItemResponse[];
  created_at: string;
}

export interface PortalQuotationListItemResponse {
  id: string;
  quotation_number: string;
  status: string;
  issue_date?: string | null;
  expiration_date?: string | null;
  total_amount: string;
  currency: string;
  created_at: string;
}

export interface PortalActionResponse {
  success: boolean;
  message: string;
  quotation_id: string;
  status: string;
}

export interface LineComment {
  id: string;
  quotation_id: string;
  quotation_item_id: string;
  author_type: 'INTERNAL_USER' | 'CUSTOMER_PORTAL';
  author_user_id?: string | null;
  author_portal_user_id?: string | null;
  author_name: string;
  comment_text: string;
  is_internal_only: boolean;
  created_at: string;
}

export interface LineCommentCreate {
  quotation_item_id: string;
  comment_text: string;
  is_internal_only?: boolean;
}

export interface ChangeRequest {
  id: string;
  quotation_id: string;
  quotation_item_id?: string | null;
  requested_by_portal_user_id: string;
  change_type: string;
  status: 'OPEN' | 'UNDER_REVIEW' | 'ACCEPTED' | 'REJECTED' | 'WITHDRAWN';
  requested_discount_percent?: number | string | null;
  requested_quantity?: number | string | null;
  request_details: string;
  response_note?: string | null;
  reviewed_by_user_id?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface ChangeRequestCreate {
  quotation_item_id?: string | null;
  change_type: 'quantity_change' | 'counter_discount' | 'validity_extension' | 'general_terms';
  requested_discount_percent?: number;
  requested_quantity?: number;
  request_details: string;
}

export interface ChangeRequestReview {
  status: 'ACCEPTED' | 'REJECTED';
  response_note?: string;
}

export interface CounterDiscountApply {
  quotation_item_id?: string | null;
  requested_discount_percent: number;
  change_reason: string;
}

export interface QuotationVersion {
  id: string;
  quotation_id: string;
  version_number: number;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  gross_margin?: string | null;
  margin_percent?: string | null;
  change_reason: string;
  snapshot_payload: Record<string, any>;
  created_by_user_id?: string | null;
  created_at: string;
}

export interface ApprovalAuditLog {
  id: string;
  quotation_id: string;
  approval_id?: string | null;
  event_type: string;
  actor_user_id?: string | null;
  actor_name?: string | null;
  previous_status?: string | null;
  new_status: string;
  reason?: string | null;
  notes?: string | null;
  approval_rule_id?: string | null;
  approval_level: number;
  created_at: string;
}

// --- Original Phases 36–45 (Inventory, Fulfillment & Hybrid Billing) ---

export interface Warehouse {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  address?: string | null;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WarehouseCreate {
  code: string;
  name: string;
  address?: string | null;
  priority?: number;
  is_active?: boolean;
}

export interface ProductVariant {
  id: string;
  organization_id: string;
  product_id: string;
  sku: string;
  name: string;
  unit_price_override?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductVariantCreate {
  product_id: string;
  sku: string;
  name: string;
  unit_price_override?: number | string | null;
  is_active?: boolean;
}

export interface StockReceiptRequest {
  warehouse_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity: number;
  notes?: string | null;
}

export interface InventoryStock {
  id: string;
  organization_id: string;
  warehouse_id: string;
  product_id: string;
  variant_id?: string | null;
  location_code?: string | null;
  on_hand_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  created_at: string;
  updated_at: string;
}

export interface InventoryMovement {
  id: string;
  organization_id: string;
  warehouse_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity: number;
  movement_type: 'RECEIPT' | 'RESERVATION' | 'RELEASE' | 'SHIPMENT' | 'ADJUSTMENT';
  reference_type?: string | null;
  reference_id?: string | null;
  actor_id?: string | null;
  actor_name?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface LineAvailabilityItem {
  quotation_item_id: string;
  product_id: string;
  variant_id?: string | null;
  product_name: string;
  requested_quantity: number;
  on_hand_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  shortfall_quantity: number;
  status: 'AVAILABLE' | 'PARTIALLY_AVAILABLE' | 'OUT_OF_STOCK';
}

export interface QuotationAvailabilitySummary {
  quotation_id: string;
  overall_status: 'AVAILABLE' | 'PARTIALLY_AVAILABLE' | 'OUT_OF_STOCK';
  total_requested: number;
  total_available: number;
  total_shortfall: number;
  line_availabilities: LineAvailabilityItem[];
}

export interface InventoryReservation {
  id: string;
  organization_id: string;
  quotation_id: string;
  quotation_item_id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  quantity: number;
  status: 'ACTIVE' | 'RELEASED' | 'CONSUMED' | 'EXPIRED';
  expires_at?: string | null;
  created_at: string;
}

export interface WarehouseAllocation {
  id: string;
  organization_id: string;
  quotation_id: string;
  quotation_item_id: string;
  warehouse_id: string;
  allocated_quantity: number;
  allocation_strategy: 'SINGLE_WAREHOUSE' | 'MINIMAL_SPLIT' | 'MANUAL_OVERRIDE';
  status: 'ALLOCATED' | 'FULFILLED' | 'CANCELLED';
  created_at: string;
}

export interface SmartAllocationSummary {
  quotation_id: string;
  is_fully_allocated: boolean;
  total_requested: number;
  total_allocated: number;
  total_shortfall: number;
  allocations: WarehouseAllocation[];
}

export interface ManualOverrideRequest {
  quotation_id: string;
  quotation_item_id: string;
  new_warehouse_id: string;
  allocated_quantity: number;
  reason: string;
}

export interface FulfillmentOverrideAudit {
  id: string;
  organization_id: string;
  quotation_id: string;
  quotation_item_id?: string | null;
  actor_id: string;
  actor_name: string;
  original_allocation: Record<string, any>;
  new_allocation: Record<string, any>;
  reason: string;
  created_at: string;
}

export interface ShipmentLine {
  id: string;
  organization_id: string;
  shipment_id: string;
  quotation_item_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity: number;
  created_at: string;
}

export interface Shipment {
  id: string;
  organization_id: string;
  shipment_number: string;
  quotation_id: string;
  warehouse_id: string;
  status: 'DRAFT' | 'PACKED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';
  carrier?: string | null;
  tracking_number?: string | null;
  shipped_at?: string | null;
  expected_delivery_date?: string | null;
  actual_delivery_date?: string | null;
  lines: ShipmentLine[];
  created_at: string;
}

export interface ShipmentCreateRequest {
  quotation_id: string;
  warehouse_id: string;
  carrier?: string;
  tracking_number?: string;
  expected_delivery_date?: string;
}

export interface Backorder {
  id: string;
  organization_id: string;
  backorder_number: string;
  quotation_id: string;
  quotation_item_id: string;
  customer_id: string;
  product_id: string;
  variant_id?: string | null;
  requested_quantity: number;
  fulfilled_quantity: number;
  remaining_quantity: number;
  warehouse_id?: string | null;
  status: 'OPEN' | 'PARTIALLY_FULFILLED' | 'FULFILLED' | 'CANCELLED';
  promised_delivery_date?: string | null;
  created_at: string;
}

export interface BackorderConsolidationSummary {
  customer_id: string;
  total_open_backorders: number;
  total_remaining_quantity: number;
  backorders: Backorder[];
}

export interface DeliveryPromise {
  id: string;
  organization_id: string;
  quotation_id: string;
  shipment_id?: string | null;
  backorder_id?: string | null;
  promised_date: string;
  expected_date: string;
  actual_date?: string | null;
  status: 'ON_TIME' | 'AT_RISK' | 'DELAYED' | 'MET' | 'MISSED';
  slippage_days: number;
  notes?: string | null;
  created_at: string;
}

export interface LineBillingClassification {
  quotation_item_id: string;
  product_id: string;
  product_name: string;
  billing_type: 'ONE_TIME' | 'RECURRING';
  unit_price: string;
  quantity: number;
  line_total: string;
}

export interface BillingClassification {
  id: string;
  organization_id: string;
  quotation_id: string;
  commercial_model: 'ONE_TIME' | 'RECURRING' | 'HYBRID';
  one_time_total: string;
  recurring_monthly_total: string;
  billing_frequency: string;
  line_classifications: LineBillingClassification[];
  created_at: string;
}

export interface InvoiceItem {
  id: string;
  organization_id: string;
  invoice_id: string;
  product_id?: string | null;
  product_variant_id?: string | null;
  quotation_item_id?: string | null;
  description: string;
  quantity: number;
  unit_price: string;
  discount_amount: string;
  tax_amount: string;
  line_subtotal: string;
  line_total: string;
  billing_type: 'ONE_TIME' | 'RECURRING';
  created_at: string;
}

export interface Invoice {
  id: string;
  organization_id: string;
  invoice_number: string;
  customer_id: string;
  quotation_id?: string | null;
  currency: string;
  invoice_date: string;
  due_date: string;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  total: string;
  amount_paid: string;
  amount_due: string;
  status: 'DRAFT' | 'ISSUED' | 'PARTIALLY_PAID' | 'PAID' | 'OVERDUE' | 'VOID';
  items?: InvoiceItem[];
  created_at: string;
  updated_at: string;
}

export interface InvoiceItemCreate {
  product_id?: string | null;
  product_variant_id?: string | null;
  quotation_item_id?: string | null;
  description: string;
  quantity: number;
  unit_price: number | string;
  discount_amount?: number | string;
  tax_amount?: number | string;
  billing_type?: 'ONE_TIME' | 'RECURRING';
}

export interface InvoiceCreate {
  customer_id: string;
  quotation_id?: string | null;
  currency?: string;
  invoice_date?: string | null;
  due_date?: string | null;
  items: InvoiceItemCreate[];
}

export interface Payment {
  id: string;
  organization_id: string;
  payment_number: string;
  invoice_id: string;
  customer_id: string;
  payment_method: 'CREDIT_CARD' | 'BANK_TRANSFER' | 'CHECK' | 'ACH' | 'CASH';
  amount: string;
  currency: string;
  payment_date: string;
  transaction_reference?: string | null;
  status: 'RECORDED' | 'FAILED' | 'REFUNDED' | 'PARTIALLY_REFUNDED';
  notes?: string | null;
  recorded_by_user_id?: string | null;
  created_at: string;
}

export interface PaymentCreate {
  invoice_id: string;
  payment_method: 'CREDIT_CARD' | 'BANK_TRANSFER' | 'CHECK' | 'ACH' | 'CASH';
  amount: number | string;
  payment_date?: string | null;
  transaction_reference?: string | null;
  notes?: string | null;
}

export interface BillingSchedule {
  id: string;
  organization_id: string;
  subscription_id: string;
  billing_period_start: string;
  billing_period_end: string;
  billing_date: string;
  amount: string;
  status: 'SCHEDULED' | 'DUE' | 'INVOICED' | 'PAID' | 'SKIPPED' | 'CANCELLED';
  invoice_id?: string | null;
  created_at: string;
}

export interface Subscription {
  id: string;
  organization_id: string;
  subscription_number: string;
  customer_id: string;
  quotation_id?: string | null;
  quotation_item_id?: string | null;
  product_id: string;
  variant_id?: string | null;
  plan_name: string;
  quantity: number;
  unit_price: string;
  billing_interval: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  start_date: string;
  next_billing_date: string;
  end_date?: string | null;
  status: 'TRIAL' | 'ACTIVE' | 'PAUSED' | 'CANCELLED' | 'EXPIRED';
  schedules?: BillingSchedule[];
  created_at: string;
  updated_at: string;
}

export interface SubscriptionCreate {
  customer_id: string;
  product_id: string;
  variant_id?: string | null;
  quotation_id?: string | null;
  quotation_item_id?: string | null;
  plan_name: string;
  quantity: number;
  unit_price: number | string;
  billing_interval: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  start_date?: string | null;
}

export interface ProrationCalculation {
  subscription_id: string;
  new_quantity: number;
  new_unit_price: string;
  effective_date: string;
  billing_period_start: string;
  billing_period_end: string;
  total_period_days: number;
  remaining_days: number;
  unused_amount: string;
  new_amount: string;
  net_prorated_amount: string;
}

export interface SubscriptionProration {
  id: string;
  organization_id: string;
  subscription_id: string;
  old_quantity: number;
  new_quantity: number;
  old_unit_price: string;
  new_unit_price: string;
  billing_period_start: string;
  billing_period_end: string;
  effective_date: string;
  total_period_days: number;
  remaining_days: number;
  prorated_amount: string;
  notes?: string | null;
  created_at: string;
}

export interface SubscriptionCancellation {
  id: string;
  organization_id: string;
  subscription_id: string;
  cancellation_type: 'IMMEDIATE' | 'END_OF_PERIOD';
  reason: string;
  effective_date: string;
  notes?: string | null;
  created_at: string;
}

export interface CreditNoteItem {
  id: string;
  organization_id: string;
  credit_note_id: string;
  description: string;
  quantity: number;
  unit_price: string;
  amount: string;
  created_at: string;
}

export interface CreditNote {
  id: string;
  organization_id: string;
  credit_note_number: string;
  invoice_id: string;
  customer_id: string;
  reason: string;
  subtotal: string;
  tax_total: string;
  total: string;
  status: 'ISSUED' | 'APPLIED' | 'VOID';
  items: CreditNoteItem[];
  created_at: string;
  updated_at: string;
}

export interface CreditNoteCreate {
  invoice_id: string;
  reason: string;
  items: {
    description: string;
    quantity: number;
    unit_price: number | string;
  }[];
}

export interface PaymentRefund {
  id: string;
  organization_id: string;
  refund_number: string;
  payment_id: string;
  credit_note_id?: string | null;
  amount: string;
  reason: string;
  refund_date: string;
  status: 'PROCESSED' | 'CANCELLED';
  created_at: string;
}

// Phase 53: Deal Health Engine
export interface DealHealthSnapshot {
  id: string;
  organization_id: string;
  deal_id: string;
  health_score: number;
  health_status: 'HEALTHY' | 'ATTENTION' | 'CRITICAL' | 'STALLED';
  positive_drivers: string[];
  negative_drivers: string[];
  recommended_actions: string[];
  evaluated_at: string;
  created_at: string;
}

// Phase 54: Stalled Quote Detection
export interface StalledQuoteItem {
  quotation_id: string;
  quotation_number: string;
  customer_id: string;
  customer_name: string;
  total_amount: string;
  status: string;
  quotation_date: string;
  days_inactive: number;
  stall_reason: string;
  stall_category: 'ATTENTION' | 'CRITICAL';
}

export interface StalledQuotesResponse {
  stalled_quotes: StalledQuoteItem[];
  total_stalled_count: number;
  generated_at: string;
}

// Phase 55: Discount Anomaly Monitoring
export interface DiscountAnomalyItem {
  quotation_id: string;
  quotation_number: string;
  customer_id: string;
  customer_name: string;
  blended_discount_percent: string;
  historical_customer_avg_discount?: string | null;
  historical_product_avg_discount?: string | null;
  organization_avg_discount: string;
  variance_percent: string;
  anomaly_score: number;
  severity: 'NORMAL' | 'WATCH' | 'ANOMALOUS' | 'CRITICAL';
  insufficient_historical_data: boolean;
  sample_size: number;
  evidence: string[];
  created_at: string;
}

export interface DiscountAnomaliesResponse {
  anomalies: DiscountAnomalyItem[];
  anomalous_count: number;
  generated_at: string;
}

// Phase 56: Delivery Slippage Monitoring
export interface DeliverySlippageItem {
  delivery_promise_id: string;
  quotation_id: string;
  quotation_number: string;
  customer_id: string;
  customer_name: string;
  shipment_id?: string | null;
  backorder_id?: string | null;
  promised_date: string;
  expected_date: string;
  actual_date?: string | null;
  slippage_days: number;
  status: 'ON_TRACK' | 'AT_RISK' | 'DELAYED' | 'DELIVERED';
  root_cause: string;
  evidence: string[];
}

export interface DeliverySlippageResponse {
  deliveries: DeliverySlippageItem[];
  at_risk_count: number;
  delayed_count: number;
  generated_at: string;
}

// Phase 57: Nudges & Escalations
export type NudgeStatus = 'CREATED' | 'OPEN' | 'ACKNOWLEDGED' | 'COMPLETED' | 'DISMISSED' | 'ESCALATED';

export interface NudgeHistory {
  id: string;
  organization_id: string;
  nudge_id: string;
  from_status?: NudgeStatus | null;
  to_status: NudgeStatus;
  user_id?: string | null;
  user_name?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface Nudge {
  id: string;
  organization_id: string;
  nudge_type: string;
  severity: 'INFO' | 'WARNING' | 'URGENT' | 'CRITICAL';
  title: string;
  message: string;
  entity_type: string;
  entity_id: string;
  dedup_hash: string;
  status: NudgeStatus;
  assigned_user_id?: string | null;
  action_payload?: Record<string, any> | null;
  escalated_at?: string | null;
  history?: NudgeHistory[];
  created_at: string;
  updated_at: string;
}

export interface NudgesResponse {
  nudges: Nudge[];
  open_count: number;
  urgent_count: number;
  generated_at: string;
}

// Phase 58 & 59: Reporting & Analytics
export interface ReportDomainSales {
  pipeline_total_value: string;
  open_deals_count: number;
  won_deals_count: number;
  lost_deals_count: number;
  won_revenue: string;
  win_rate_percent: string;
}

export interface ReportDomainQuotations {
  total_quotations_count: number;
  draft_count: number;
  sent_count: number;
  accepted_count: number;
  rejected_count: number;
  expired_count: number;
  conversion_rate_percent: string;
  average_quotation_value: string;
}

export interface ReportDomainFulfillment {
  total_deliveries: number;
  on_track_count: number;
  at_risk_count: number;
  delayed_count: number;
  delivered_count: number;
  on_time_delivery_percent: string;
  average_slippage_days: string;
}

export interface ReportDomainCommercial {
  gross_revenue: string;
  gross_margin: string;
  gross_margin_percent: string;
  total_discounts_given: string;
  average_discount_percent: string;
  pending_approvals_count: number;
}

export interface ReportDomainSubscriptions {
  active_subscriptions_count: number;
  monthly_recurring_revenue: string;
  annual_recurring_revenue: string;
  churn_count: number;
  churn_rate_percent: string;
}

export interface ExecutiveReportSummaryResponse {
  period: string;
  sales: ReportDomainSales;
  quotations: ReportDomainQuotations;
  fulfillment: ReportDomainFulfillment;
  commercial: ReportDomainCommercial;
  subscriptions: ReportDomainSubscriptions;
  generated_at: string;
}

export interface ExecutiveAnalyticsResponse {
  organization_id: string;
  period: string;
  reporting: ExecutiveReportSummaryResponse;
  monitoring_summary: {
    stalled_quotes_count: number;
    discount_anomalies_count: number;
    delivery_slippage_count: number;
    open_nudges_count: number;
    urgent_nudges_count: number;
  };
  generated_at: string;
}




