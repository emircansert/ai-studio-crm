from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    detail: str


class ArchiveRequest(BaseModel):
    reason: str | None = None


class LeaderboardResetRequest(BaseModel):
    scope: str
    user_id: UUID | None = None
    reason: str
    dry_run: bool = True


class LeaderboardResetResponse(BaseModel):
    scope: str
    user_id: UUID | None = None
    affected_count: int
    crm_activity_affected_count: int = 0
    champion_activity_affected_count: int = 0
    dry_run: bool
    reset_applied: bool


class ChampionActivityBase(BaseModel):
    user_id: UUID
    category: str
    activity_type: str
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    activity_date: datetime
    quantity: int = 1
    source: str = "ADMIN_RECORDED"
    status: str = "ACTIVE"
    evidence_url: str | None = None
    notes: str | None = None


class ChampionActivityCreate(ChampionActivityBase):
    pass


class ChampionActivityUpdate(BaseModel):
    user_id: UUID | None = None
    category: str | None = None
    activity_type: str | None = None
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    activity_date: datetime | None = None
    quantity: int | None = None
    source: str | None = None
    status: str | None = None
    evidence_url: str | None = None
    notes: str | None = None


class ArchiveFields(BaseModel):
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by_user_id: UUID | None = None
    archive_reason: str | None = None


class ChampionActivityRead(ChampionActivityBase, ArchiveFields, ORMModel):
    id: UUID
    created_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "USER"
    is_active: bool = True


class UserCreate(UserBase):
    """Users carry no credential: identity comes from Microsoft Entra ID."""


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class AdminUserCreate(BaseModel):
    """Pre-provision a CRM user. No password: sign-in is Entra ID only."""

    email: str
    full_name: str
    role: str = "USER"


class AdminUserRoleUpdate(BaseModel):
    role: str


class UserRead(UserBase, ORMModel):
    id: UUID
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SectionAccessDefinition(BaseModel):
    key: str
    label: str
    admin_only: bool = False


class UserSectionAccessBulkUpdate(BaseModel):
    access: dict[str, str]


class UserSectionAccessResponse(BaseModel):
    user_id: UUID
    access: dict[str, str]


class UserAccessMatrixRow(BaseModel):
    user: UserRead
    access: dict[str, str]


class UserAccessMatrixResponse(BaseModel):
    sections: list[SectionAccessDefinition]
    users: list[UserAccessMatrixRow]


class CurrentUserSectionAccessResponse(BaseModel):
    sections: list[SectionAccessDefinition]
    access: dict[str, str]


class StatusBase(BaseModel):
    code: str
    label: str
    status_group: str
    sort_order: int = 0
    is_terminal: bool = False


class StatusCreate(StatusBase):
    pass


class StatusUpdate(BaseModel):
    label: str | None = None
    status_group: str | None = None
    sort_order: int | None = None
    is_terminal: bool | None = None


class StatusRead(StatusBase, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class OrganizationBase(BaseModel):
    name: str
    normalized_name: str | None = None
    organization_type: str
    organization_subtype: str | None = None
    category_code: str | None = None
    category_label: str | None = None
    vertical_text: str | None = None
    website_url: str | None = None
    website_domain: str | None = None
    geography_text: str | None = None
    country_codes: list[str] | None = None
    source_text: str | None = None
    added_by_text: str | None = None
    solution_summary: str | None = None
    lifecycle_status_id: UUID | None = None
    relationship_status_id: UUID | None = None
    last_contact_date: date | None = None
    raw_import_ref: UUID | None = None
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
    ai_summary: str | None = None
    ai_tags: list[str] | None = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    normalized_name: str | None = None
    organization_type: str | None = None
    organization_subtype: str | None = None
    category_code: str | None = None
    category_label: str | None = None
    vertical_text: str | None = None
    website_url: str | None = None
    website_domain: str | None = None
    geography_text: str | None = None
    country_codes: list[str] | None = None
    source_text: str | None = None
    added_by_text: str | None = None
    solution_summary: str | None = None
    lifecycle_status_id: UUID | None = None
    status_code: str | None = None
    relationship_status_id: UUID | None = None
    last_contact_date: date | None = None
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
    ai_summary: str | None = None
    ai_tags: list[str] | None = None


class OrganizationRead(OrganizationBase, ArchiveFields, ORMModel):
    id: UUID
    normalized_name: str
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ContactBase(BaseModel):
    organization_id: UUID
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    contact_source: str = "MANUAL"
    raw_contact_text: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    organization_id: UUID | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    contact_source: str | None = None
    raw_contact_text: str | None = None


class ContactRead(ContactBase, ArchiveFields, ORMModel):
    id: UUID
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class OrganizationBorusanFitCreate(BaseModel):
    borusan_company_id: UUID
    fit_level: str = "RELEVANT"
    fit_reason: str | None = None
    source: str = "MANUAL"
    raw_value: str | None = None


class OrganizationBorusanFitUpdate(BaseModel):
    borusan_company_id: UUID | None = None
    fit_level: str | None = None
    fit_reason: str | None = None
    source: str | None = None
    raw_value: str | None = None


class OrganizationBorusanFitRead(ArchiveFields, ORMModel):
    id: UUID
    organization_id: UUID
    borusan_company_id: UUID
    fit_level: str
    fit_reason: str | None = None
    source: str
    raw_value: str | None = None


class BorusanCompanyBase(BaseModel):
    code: str
    name: str
    english_name: str | None = None
    legacy_excel_column: str | None = None
    aliases: list[str] | None = None
    is_active: bool = True


class BorusanCompanyCreate(BorusanCompanyBase):
    pass


class BorusanCompanyUpdate(BaseModel):
    name: str | None = None
    english_name: str | None = None
    legacy_excel_column: str | None = None
    aliases: list[str] | None = None
    is_active: bool | None = None


class BorusanCompanyRead(BorusanCompanyBase, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class TagBase(BaseModel):
    code: str
    label: str
    tag_group: str


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    label: str | None = None
    tag_group: str | None = None


class TagRead(TagBase, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class OpportunityBase(BaseModel):
    title: str
    organization_id: UUID
    borusan_company_id: UUID
    opportunity_type: str = "POC"
    stage: str
    stage_migration_note: str | None = None
    status_id: UUID | None = None
    topic: str | None = None
    terms_text: str | None = None
    value_hypothesis: str | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    last_contact_date: date | None = None
    owner_user_id: UUID | None = None
    next_action_id: UUID | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: str | None = None
    organization_id: UUID | None = None
    borusan_company_id: UUID | None = None
    opportunity_type: str | None = None
    stage: str | None = None
    stage_migration_note: str | None = None
    status_id: UUID | None = None
    topic: str | None = None
    terms_text: str | None = None
    value_hypothesis: str | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    last_contact_date: date | None = None
    owner_user_id: UUID | None = None
    next_action_id: UUID | None = None


class OpportunityRead(OpportunityBase, ArchiveFields, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class UseCaseProposalBase(BaseModel):
    title: str
    description: str | None = None
    borusan_company_id: UUID | None = None
    business_unit_text: str | None = None
    proposer_user_id: UUID | None = None
    related_organization_id: UUID | None = None
    problem_area: str | None = None
    proposed_solution: str | None = None
    expected_impact: str | None = None
    status: str = "IDEA"
    stage: str = "IDEA"
    priority: str = "MEDIUM"


class UseCaseProposalCreate(UseCaseProposalBase):
    pass


class UseCaseProposalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    borusan_company_id: UUID | None = None
    business_unit_text: str | None = None
    proposer_user_id: UUID | None = None
    related_organization_id: UUID | None = None
    problem_area: str | None = None
    proposed_solution: str | None = None
    expected_impact: str | None = None
    status: str | None = None
    stage: str | None = None
    priority: str | None = None


class UseCaseProposalRead(UseCaseProposalBase, ArchiveFields, ORMModel):
    id: UUID
    created_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class EventBase(BaseModel):
    name: str
    starts_on: date | None = None
    ends_on: date | None = None
    date_text: str | None = None
    location_text: str
    geography_text: str | None = None
    area_text: str | None = None
    ai_program_relevance: str = "UNKNOWN"
    value_creation_potential: str = "UNKNOWN"
    comments: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    date_text: str | None = None
    location_text: str | None = None
    geography_text: str | None = None
    area_text: str | None = None
    ai_program_relevance: str | None = None
    value_creation_potential: str | None = None
    comments: str | None = None


class EventRead(EventBase, ArchiveFields, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ProgramActivityParticipantBase(BaseModel):
    program_activity_id: UUID | None = None
    user_id: UUID
    role: str | None = None
    attendance_status: str | None = None
    completion_status: str | None = None
    notes: str | None = None


class ProgramActivityParticipantCreate(ProgramActivityParticipantBase):
    pass


class ProgramActivityParticipantUpdate(BaseModel):
    user_id: UUID | None = None
    role: str | None = None
    attendance_status: str | None = None
    completion_status: str | None = None
    notes: str | None = None


class ProgramActivityParticipantRead(ProgramActivityParticipantBase, ORMModel):
    id: UUID
    program_activity_id: UUID
    recorded_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ProgramActivityBase(BaseModel):
    activity_type: str
    title: str
    description: str | None = None
    activity_date: date | None = None
    location_text: str | None = None
    owner_team: str | None = None
    tracking_owner: str | None = None


class ProgramActivityCreate(ProgramActivityBase):
    pass


class ProgramActivityUpdate(BaseModel):
    activity_type: str | None = None
    title: str | None = None
    description: str | None = None
    activity_date: date | None = None
    location_text: str | None = None
    owner_team: str | None = None
    tracking_owner: str | None = None


class ProgramActivityRead(ProgramActivityBase, ArchiveFields, ORMModel):
    id: UUID
    created_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    participants: list[ProgramActivityParticipantRead] = []


class AIToolBase(BaseModel):
    name: str
    vendor_name: str | None = None
    vendor_organization_id: UUID | None = None
    website_url: str | None = None
    category_text: str | None = None
    primary_use_case: str | None = None
    description: str | None = None
    solution_summary: str | None = None
    pricing_model: str | None = None
    deployment_type: str | None = None
    data_sensitivity_level: str | None = None
    status: str = "Identified"
    owner_notes: str | None = None
    source: str | None = "MANUAL"
    notes: str | None = None
    added_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None


class AIToolCreate(AIToolBase):
    pass


class AIToolUpdate(BaseModel):
    name: str | None = None
    vendor_name: str | None = None
    vendor_organization_id: UUID | None = None
    website_url: str | None = None
    category_text: str | None = None
    primary_use_case: str | None = None
    description: str | None = None
    solution_summary: str | None = None
    pricing_model: str | None = None
    deployment_type: str | None = None
    data_sensitivity_level: str | None = None
    status: str | None = None
    owner_notes: str | None = None
    source: str | None = None
    notes: str | None = None
    added_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None


class AIToolRead(AIToolBase, ArchiveFields, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class NoteBase(BaseModel):
    entity_type: str
    entity_id: UUID
    note_type: str = "GENERAL"
    body: str
    occurred_at: datetime | None = None
    created_by_user_id: UUID | None = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    note_type: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    created_by_user_id: UUID | None = None


class NoteRead(NoteBase, ArchiveFields, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FollowUpActionBase(BaseModel):
    entity_type: str
    entity_id: UUID
    title: str
    due_date: date | None = None
    status: str = "OPEN"
    assigned_to_user_id: UUID | None = None
    created_by_user_id: UUID | None = None
    completed_by_user_id: UUID | None = None
    completed_at: datetime | None = None


class FollowUpActionCreate(FollowUpActionBase):
    pass


class FollowUpActionUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None
    status: str | None = None
    assigned_to_user_id: UUID | None = None


class FollowUpActionRead(FollowUpActionBase, ArchiveFields, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ImportBatchBase(BaseModel):
    original_filename: str
    file_sha256: str
    uploaded_by_user_id: UUID | None = None
    status: str = "UPLOADED"
    workbook_metadata: dict[str, Any] | None = None


class ImportBatchCreate(ImportBatchBase):
    pass


class ImportBatchUpdate(BaseModel):
    status: str | None = None
    workbook_metadata: dict[str, Any] | None = None


class ImportBatchRead(ImportBatchBase, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ImportCandidateDecisionUpdate(BaseModel):
    decision_status: str
    decision_reason: str | None = None


class ImportCandidateRead(ORMModel):
    id: UUID
    import_batch_id: UUID
    import_row_id: UUID | None
    entity_type: str
    action_type: str
    match_entity_type: str | None
    match_entity_id: UUID | None
    candidate_data: dict[str, Any]
    raw_source: dict[str, Any] | None
    validation_status: str
    decision_status: str
    decision_reason: str | None
    created_at: datetime
    updated_at: datetime


class AuditLogRead(ORMModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class NotificationRead(ORMModel):
    id: UUID
    user_id: UUID
    actor_user_id: UUID | None = None
    notification_type: str
    title: str
    body: str | None = None
    entity_type: str | None = None
    entity_id: UUID | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationUnreadCount(BaseModel):
    unread_count: int


class CrmActivityEventRead(ORMModel):
    id: UUID
    actor_user_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: UUID | None = None
    title: str
    summary: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class BrandingAssetBase(BaseModel):
    asset_type: str = "LOGO"
    original_filename: str
    storage_path: str
    content_type: str
    file_size_bytes: int
    file_sha256: str
    is_active: bool = False
    uploaded_by_user_id: UUID | None = None


class BrandingAssetCreate(BrandingAssetBase):
    pass


class BrandingAssetUpdate(BaseModel):
    is_active: bool | None = None


class BrandingAssetRead(BrandingAssetBase, ORMModel):
    id: UUID
    created_at: datetime


class OrganizationDocumentRead(ArchiveFields, ORMModel):
    id: UUID
    organization_id: UUID
    uploaded_by_user_id: UUID | None = None
    document_type: str
    original_filename: str
    stored_filename: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    uploaded_at: datetime


class OpportunityDocumentRead(ArchiveFields, ORMModel):
    id: UUID
    opportunity_id: UUID
    uploaded_by_user_id: UUID | None = None
    document_type: str
    original_filename: str
    stored_filename: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    uploaded_at: datetime


class VendorBase(BaseModel):
    name: str
    category_text: str | None = None
    description: str | None = None
    contact_info: str | None = None
    website_url: str | None = None
    status: str = "PROSPECT"
    geography_text: str | None = None
    last_contact_date: date | None = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: str | None = None
    category_text: str | None = None
    description: str | None = None
    contact_info: str | None = None
    website_url: str | None = None
    status: str | None = None
    geography_text: str | None = None
    last_contact_date: date | None = None


class VendorRead(VendorBase, ArchiveFields, ORMModel):
    id: UUID
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class VendorRatingUpsert(BaseModel):
    quality_score: int = Field(ge=1, le=5)
    reliability_score: int = Field(ge=1, le=5)
    pricing_score: int = Field(ge=1, le=5)
    borusan_fit_score: int = Field(ge=1, le=5)
    comment: str | None = None
