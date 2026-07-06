from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_audit_logs,
    admin_activity,
    admin_branding,
    admin_champion_activities,
    admin_leaderboard,
    admin_users,
    ai_tools,
    auth,
    borusan_companies,
    contacts,
    dashboard,
    events,
    follow_ups,
    health,
    imports,
    leaderboard,
    network,
    notes,
    notifications,
    opportunities,
    organizations,
    program_activities,
    statuses,
    tags,
    use_cases,
    users,
    vendors,
    vocabularies,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(contacts.router)
api_router.include_router(dashboard.router)
api_router.include_router(opportunities.router)
api_router.include_router(use_cases.router, prefix="/use-cases", tags=["use-cases"])
api_router.include_router(events.router)
api_router.include_router(program_activities.router, prefix="/program-activities", tags=["program-activities"])
api_router.include_router(follow_ups.router)
api_router.include_router(network.router)
api_router.include_router(vendors.router)
api_router.include_router(notes.router)
api_router.include_router(ai_tools.router)
api_router.include_router(imports.router)
api_router.include_router(leaderboard.router)
api_router.include_router(tags.router)
api_router.include_router(users.router)
api_router.include_router(vocabularies.router)
api_router.include_router(statuses.router)
api_router.include_router(borusan_companies.router)
api_router.include_router(notifications.router)
api_router.include_router(admin_activity.router)
api_router.include_router(admin_branding.router)
api_router.include_router(admin_champion_activities.router)
api_router.include_router(admin_leaderboard.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_audit_logs.router)
