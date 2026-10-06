from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.services.volunteer_service import VolunteerService
from app.utilities.flash import flash
from . import router, templates


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    service = VolunteerService(db)
    submissions = service.list_for_review()
    redemptions = service.list_pending_redemptions()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "pending_submissions": len(submissions),
            "pending_redemptions": len(redemptions),
        },
    )


@router.get("/admin/profile", response_class=HTMLResponse)
async def admin_profile_view(request: Request, user: AdminDep):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user},
    )


@router.get("/admin/volunteer-hours", response_class=HTMLResponse)
async def admin_volunteer_hours_view(request: Request, user: AdminDep, db: SessionDep):
    submissions = VolunteerService(db).list_submissions_for_admin()
    return templates.TemplateResponse(
        request=request,
        name="volunteer_hours.html",
        context={"user": user, "submissions": submissions},
    )


@router.get("/admin/volunteer-hours/review", response_class=HTMLResponse)
async def admin_pending_volunteer_hours_view(request: Request, user: AdminDep, db: SessionDep):
    submissions = VolunteerService(db).list_for_review()
    return templates.TemplateResponse(
        request=request,
        name="volunteer_hours.html",
        context={"user": user, "submissions": submissions},
    )


@router.get("/admin/volunteer-hours/{submission_id}", response_class=HTMLResponse)
async def admin_submission_detail_view(
    request: Request,
    submission_id: int,
    user: AdminDep,
    db: SessionDep,
):
    service = VolunteerService(db)
    try:
        detail = service.get_submission_detail_for_admin(submission_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request=request,
        name="volunteer_review.html",
        context={
            "user": user,
            "detail": detail,
        },
    )


@router.get("/admin/awards", response_class=HTMLResponse)
async def admin_awards_view(request: Request, user: AdminDep, db: SessionDep):
    redemptions = VolunteerService(db).list_pending_redemptions()
    return templates.TemplateResponse(
        request=request,
        name="awards.html",
        context={"user": user, "redemptions": redemptions},
    )


@router.post("/admin/submissions/{submission_id}/review", response_class=HTMLResponse)
async def review_volunteer_submission(
    request: Request,
    submission_id: int,
    db: SessionDep,
    user: AdminDep,
    decision: str = Form(...),
    notes: str = Form(default=""),
):
    service = VolunteerService(db)
    try:
        service.review_submission(
            submission_id,
            decision,
            reviewer=user,
            notes=notes,
        )
        flash(request, f"Submission marked as {decision}.", "success")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("admin_volunteer_hours_view"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/redemptions/{redemption_id}/review", response_class=HTMLResponse)
async def review_award_redemption(
    request: Request,
    redemption_id: int,
    db: SessionDep,
    user: AdminDep,
    decision: str = Form(...),
):
    service = VolunteerService(db)
    try:
        service.review_redemption(redemption_id, decision, reviewer=user)
        flash(request, f"Award redemption marked as {decision}.", "success")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("admin_awards_view"), status_code=status.HTTP_303_SEE_OTHER)

