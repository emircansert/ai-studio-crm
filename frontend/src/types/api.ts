export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "ADMIN" | "USER" | string;
  is_active: boolean;
  last_login_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type SectionAccessLevel = "HIDDEN" | "VIEW" | "FULL";

export type SectionAccessDefinition = {
  key: string;
  label: string;
  admin_only: boolean;
};

export type CurrentUserSectionAccessResponse = {
  sections: SectionAccessDefinition[];
  access: Record<string, SectionAccessLevel>;
};

export type UserAccessMatrixRow = {
  user: User;
  access: Record<string, SectionAccessLevel>;
};

export type UserAccessMatrixResponse = {
  sections: SectionAccessDefinition[];
  users: UserAccessMatrixRow[];
};

export type UserSectionAccessResponse = {
  user_id: string;
  access: Record<string, SectionAccessLevel>;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type NotificationItem = {
  id: string;
  user_id: string;
  actor_user_id?: string | null;
  notification_type: string;
  title: string;
  body?: string | null;
  entity_type?: string | null;
  entity_id?: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
};

export type NotificationUnreadCount = {
  unread_count: number;
};

export type CrmActivityEvent = {
  id: string;
  actor_user_id?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  title: string;
  summary?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
};

export type VendorRatingCategoryAverages = {
  quality_score: number | null;
  reliability_score: number | null;
  pricing_score: number | null;
  borusan_fit_score: number | null;
};

export type VendorRatingSummary = {
  rating_count: number;
  overall_score: number | null;
  category_averages: VendorRatingCategoryAverages;
};

export type VendorRating = {
  id: string;
  vendor_id: string;
  rater: { id: string; full_name: string | null; email: string | null } | null;
  quality_score: number;
  reliability_score: number;
  pricing_score: number;
  borusan_fit_score: number;
  weighted_score: number;
  comment?: string | null;
  created_at: string;
  updated_at: string;
};

export type Vendor = {
  id: string;
  name: string;
  category_text?: string | null;
  description?: string | null;
  contact_info?: string | null;
  website_url?: string | null;
  status: string;
  geography_text?: string | null;
  last_contact_date?: string | null;
  created_by_user_id?: string | null;
  created_by_user?: { id: string; full_name: string | null; email: string | null } | null;
  added_by_display?: string | null;
  added_at?: string;
  is_archived?: boolean;
  archived_at?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
  rating_summary: VendorRatingSummary;
  rating_weights: Record<string, number>;
};

export type VendorDetail = Vendor & {
  ratings: VendorRating[];
  my_rating: VendorRating | null;
};

export type PaginatedVendors = {
  items: Vendor[];
  total_count: number;
  limit: number;
  offset: number;
  sort_by: string;
  statuses: string[];
};

export type VendorRatingUpsertResponse = {
  my_rating: VendorRating | null;
  rating_summary: VendorRatingSummary;
};

export type ImportBatch = {
  id: string;
  original_filename: string;
  file_sha256: string;
  uploaded_by_user_id?: string | null;
  status: string;
  workbook_metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ImportPreviewSheet = {
  id: string;
  sheet_name: string;
  detected_entity: string;
  header_row?: number | null;
  row_count?: number | null;
  staged_row_count: number;
  column_mapping?: Record<string, unknown> | null;
};

export type ImportSampleRow = {
  id: string;
  excel_row_number: number;
  validation_status: string;
  cleaned_values?: Record<string, unknown> | null;
  normalized_candidate?: Record<string, unknown> | null;
};

export type MissingMapping = {
  code: string;
  message: string;
  field_name?: string | null;
  raw_value?: string | null;
};

export type ImportPreview = {
  batch: {
    id: string;
    original_filename: string;
    file_sha256: string;
    status: string;
    created_at?: string | null;
    updated_at?: string | null;
    workbook_metadata?: Record<string, unknown> | null;
  };
  detected_sheets: ImportPreviewSheet[];
  row_counts_by_sheet: Record<string, number | null>;
  staged_row_counts: Record<string, number>;
  warning_counts: {
    by_severity: Record<string, number>;
    by_code: Record<string, number>;
  };
  sample_rows: Record<string, ImportSampleRow[]>;
  duplicate_candidates: Record<string, Record<string, unknown>>;
  missing_mappings_or_columns: MissingMapping[];
  status_mappings_used: Record<string, unknown>;
};

export type ImportCandidate = {
  id: string;
  import_batch_id: string;
  import_row_id?: string | null;
  entity_type: string;
  action_type: string;
  match_entity_type?: string | null;
  match_entity_id?: string | null;
  candidate_data: Record<string, unknown>;
  raw_source?: Record<string, unknown> | null;
  validation_status: string;
  decision_status: string;
  decision_reason?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ImportCandidatesPreview = {
  batch: {
    id: string;
    status: string;
    original_filename: string;
    file_sha256: string;
  };
  candidate_counts_by_entity_type: Record<string, number>;
  action_counts: Record<string, number>;
  validation_counts: Record<string, number>;
  decision_counts: Record<string, number>;
  candidates_by_entity_type: Record<string, ImportCandidate[]>;
  needs_review: ImportCandidate[];
  duplicate_match_summary: Record<string, number>;
  warnings: Array<Record<string, unknown>>;
  can_commit: boolean;
};

export type CommitResult = {
  batch_id: string;
  status: string;
  committed_counts: Record<string, number>;
};

export type Organization = {
  id: string;
  name: string;
  normalized_name: string;
  organization_type: string;
  organization_subtype?: string | null;
  category_code?: string | null;
  category_label?: string | null;
  category?: { code?: string | null; label?: string | null } | null;
  vertical_text?: string | null;
  website_url?: string | null;
  website_domain?: string | null;
  geography_text?: string | null;
  source_text?: string | null;
  added_by_text?: string | null;
  solution_summary?: string | null;
  lifecycle_status_id?: string | null;
  relationship_status_id?: string | null;
  lifecycle_status?: StatusRef | null;
  relationship_status?: StatusRef | null;
  borusan_fit_summary?: BorusanFitSummary[];
  tags_summary?: TagSummary[];
  expertise_text?: string | null;
  primary_contact?: Contact | null;
  notes_preview?: string | null;
  contact_count?: number;
  note_count?: number;
  opportunity_count?: number;
  deck_count?: number;
  open_follow_up_count?: number;
  contacts?: Contact[];
  notes?: Note[];
  opportunities?: OrganizationOpportunity[];
  tags?: TagSummary[];
  raw_source_reference?: Record<string, unknown> | null;
  created_by_user_id?: string | null;
  updated_by_user_id?: string | null;
  created_by_user?: UserRef | null;
  updated_by_user?: UserRef | null;
  added_by_display?: string | null;
  added_at?: string | null;
  last_contact_date?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type UserRef = {
  id: string;
  full_name?: string | null;
  email?: string | null;
};

export type PaginatedOrganizations = {
  items: Organization[];
  total_count: number;
  limit: number;
  offset: number;
  sort_by: string;
};

export type CategoryOption = {
  code?: string | null;
  label?: string | null;
  source?: string | null;
};

export type StatusRef = {
  id: string;
  code: string;
  label: string;
  status_group: string;
};

export type TagSummary = {
  id: string;
  code: string;
  label: string;
  tag_group: string;
  source?: string | null;
};

export type BorusanFitSummary = {
  id: string;
  borusan_company_id: string;
  borusan_company_code?: string;
  borusan_company_name?: string;
  fit_level: string;
  fit_reason?: string | null;
  source: string;
  raw_value?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
};

export type Contact = {
  id: string;
  organization_id: string;
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  title?: string | null;
  raw_contact_text?: string | null;
  contact_source: string;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type Note = {
  id: string;
  entity_type: string;
  entity_id: string;
  note_type: string;
  body: string;
  occurred_at?: string | null;
  created_by_user_id?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type OrganizationOpportunity = {
  id: string;
  title: string;
  stage: string;
  topic?: string | null;
  borusan_company_id?: string | null;
  status_id?: string | null;
  last_contact_date?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type EventRecord = {
  id: string;
  name: string;
  starts_on?: string | null;
  ends_on?: string | null;
  date_text?: string | null;
  location_text: string;
  geography_text?: string | null;
  area_text?: string | null;
  ai_program_relevance: string;
  value_creation_potential: string;
  comments?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type Opportunity = {
  id: string;
  title: string;
  organization_id: string;
  borusan_company_id: string;
  opportunity_type?: string;
  stage: string;
  stage_migration_note?: string | null;
  status_id?: string | null;
  topic?: string | null;
  terms_text?: string | null;
  value_hypothesis?: string | null;
  expected_start_date?: string | null;
  expected_end_date?: string | null;
  last_contact_date?: string | null;
  owner_user_id?: string | null;
  next_action_id?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type OpportunityDocument = {
  id: string;
  opportunity_id: string;
  uploaded_by_user_id?: string | null;
  uploaded_by_user?: UserRef | null;
  document_type: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  uploaded_at: string;
  download_url?: string;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
};

export type StatusOption = {
  id: string;
  code: string;
  label: string;
  status_group: string;
  sort_order: number;
  is_terminal: boolean;
};

export type BorusanCompany = {
  id: string;
  code: string;
  name: string;
  english_name?: string | null;
  is_active: boolean;
};

export type AITool = {
  id: string;
  name: string;
  vendor_name?: string | null;
  vendor_organization_id?: string | null;
  website_url?: string | null;
  category_text?: string | null;
  primary_use_case?: string | null;
  description?: string | null;
  solution_summary?: string | null;
  pricing_model?: string | null;
  deployment_type?: string | null;
  data_sensitivity_level?: string | null;
  status: string;
  owner_notes?: string | null;
  source?: string | null;
  notes?: string | null;
  added_by_user_id?: string | null;
  updated_by_user_id?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardSummary = {
  total_organizations: number;
  total_startups: number;
  total_vendors: number;
  total_opportunities: number;
  total_events: number;
  open_follow_ups?: number;
  overdue_follow_ups?: number;
  total_startup_decks?: number;
  total_network_institutions: number;
  active_imported_batches: number;
  latest_import_status?: string | null;
  latest_import_filename?: string | null;
  top_borusan_company_fit_counts: Array<{ code: string; name: string; count: number }>;
  top_champion?: ChampionLeaderboardRow | null;
  my_champion_score?: ChampionLeaderboardRow | null;
};

export type OrganizationDocument = {
  id: string;
  organization_id: string;
  uploaded_by_user_id?: string | null;
  uploaded_by_user?: UserRef | null;
  document_type: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  uploaded_at: string;
  download_url?: string;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
};

export type BrandingAsset = {
  id: string;
  asset_type: string;
  original_filename: string;
  storage_path: string;
  content_type: string;
  file_size_bytes: number;
  file_sha256: string;
  is_active: boolean;
  uploaded_by_user_id?: string | null;
  created_at: string;
  content_url?: string;
};

export type LeaderboardRow = {
  rank: number | null;
  user_id: string;
  full_name: string;
  email: string;
  total_points: number;
  organizations_created: number;
  contacts_created: number;
  notes_created: number;
  borusan_fits_created: number;
  opportunities_created: number;
  events_created: number;
  updates_count: number;
  follow_ups_completed?: number;
  last_contribution_at?: string | null;
};

export type FollowUp = {
  id: string;
  entity_type: string;
  entity_id: string;
  title: string;
  due_date?: string | null;
  status: "OPEN" | "DONE" | "CANCELLED" | string;
  assigned_to_user_id?: string | null;
  created_by_user_id?: string | null;
  completed_by_user_id?: string | null;
  completed_at?: string | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  actor_user_id?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  before_data?: Record<string, unknown> | null;
  after_data?: Record<string, unknown> | null;
  created_at: string;
};

export type LeaderboardResponse = {
  period: string;
  metric: string;
  items: LeaderboardRow[];
  total_users: number;
  manual_only: boolean;
};

export type ChampionScoreRule = {
  category: string;
  label: string;
  helper_label?: string | null;
  weight: number;
  task: string;
  kpi: string;
  tracking_owner: string;
  qualifying_activity_types: string[];
  thresholds: string;
  note?: string | null;
};

export type ChampionWeightedBreakdown = {
  label: string;
  weight: number;
  raw_count: number;
  category_score: number;
  weighted_score: number;
};

export type ChampionLeaderboardRow = {
  rank: number | null;
  user_id: string;
  full_name: string;
  email: string;
  champion_score: number;
  crm_activity_points: number;
  crm_activity_points_role?: string;
  crm_activity_breakdown?: Record<string, number>;
  recent_crm_activity_evidence?: Array<{
    contribution_type: string;
    entity_type: string;
    entity_id?: string | null;
    points: number;
    occurred_at?: string | null;
  }>;
  vision_strategy_score: number;
  ecosystem_library_score: number;
  ecosystem_library_raw_count?: number;
  startup_scouting_score: number;
  case_study_score: number;
  event_participation_score: number;
  training_score: number;
  weighted_breakdown: Record<string, ChampionWeightedBreakdown>;
  raw_counts: Record<string, number>;
  activity_type_counts?: Record<string, number>;
  last_activity_at?: string | null;
  missing_targets?: string[];
};

export type ChampionLeaderboardResponse = {
  period: string;
  items: ChampionLeaderboardRow[];
  total_users: number;
  scorecard: ChampionScoreRule[];
};

export type ChampionActivity = {
  id: string;
  user_id: string;
  user?: UserRef | null;
  category: string;
  activity_type: string;
  related_entity_type?: string | null;
  related_entity_id?: string | null;
  activity_date: string;
  quantity: number;
  source: string;
  status: string;
  evidence_url?: string | null;
  notes?: string | null;
  created_by_user_id?: string | null;
  created_by_user?: UserRef | null;
  is_archived?: boolean;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archive_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type ChampionActivitiesResponse = {
  items: ChampionActivity[];
  limit: number;
  offset: number;
};

export type LeaderboardResetResponse = {
  scope: string;
  user_id?: string | null;
  affected_count: number;
  crm_activity_affected_count?: number;
  champion_activity_affected_count?: number;
  dry_run: boolean;
  reset_applied: boolean;
};

export type UseCaseProposal = {
  id: string;
  title: string;
  description?: string | null;
  borusan_company_id?: string | null;
  borusan_company?: { id: string; code: string; name: string } | null;
  business_unit_text?: string | null;
  proposer_user_id?: string | null;
  proposer_user?: UserRef | null;
  related_organization_id?: string | null;
  related_organization?: { id: string; name: string } | null;
  problem_area?: string | null;
  proposed_solution?: string | null;
  expected_impact?: string | null;
  status: string;
  stage: string;
  priority: string;
  created_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
  is_archived?: boolean;
};

export type UseCasesResponse = {
  items: UseCaseProposal[];
  limit: number;
  offset: number;
};

export type ProgramActivityParticipant = {
  id: string;
  program_activity_id: string;
  user_id: string;
  user?: UserRef | null;
  role?: string | null;
  attendance_status?: string | null;
  completion_status?: string | null;
  notes?: string | null;
  recorded_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type ProgramActivity = {
  id: string;
  activity_type: "EVENT" | "TRAINING" | string;
  title: string;
  description?: string | null;
  activity_date?: string | null;
  location_text?: string | null;
  owner_team?: string | null;
  tracking_owner?: string | null;
  created_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
  is_archived?: boolean;
  participant_count?: number;
  participants?: ProgramActivityParticipant[];
};

export type ProgramActivitiesResponse = {
  items: ProgramActivity[];
  limit: number;
  offset: number;
};
