from datetime import date

from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.services.volunteer_service import VolunteerService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    service = VolunteerService(db)
    student = service.get_or_create_student_for_user(user)
    summary = service.get_student_summary(student.id)
    milestones = service.list_milestones_for_student(student.id)
    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "summary": summary,
            "milestones": milestones,
        },
    )


@router.get("/app/profile", response_class=HTMLResponse)
async def user_profile_view(request: Request, user: AuthDep):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user},
    )


@router.get("/app/awards", response_class=HTMLResponse)
async def user_awards_view(request: Request, user: AuthDep, db: SessionDep):
    service = VolunteerService(db)
    student = service.get_or_create_student_for_user(user)
    awards = service.list_awards_for_student(student.id)
    return templates.TemplateResponse(
        request=request,
        name="awards.html",
        context={"user": user, "awards": awards},
    )


@router.get("/app/volunteer-hours", response_class=HTMLResponse)
async def user_volunteer_hours_view(request: Request, user: AuthDep, db: SessionDep):
    service = VolunteerService(db)
    student = service.get_or_create_student_for_user(user)
    return templates.TemplateResponse(
        request=request,
        name="volunteer_hours.html",
        context={
            "user": user,
            "summary": service.get_student_summary(student.id),
            "submissions": service.list_for_student(student.id),
        },
    )


@router.get("/app/milestones/{milestone_id}", response_class=HTMLResponse)
async def milestone_detail_view(
    request: Request,
    milestone_id: int,
    user: AuthDep,
    db: SessionDep,
):
    service = VolunteerService(db)
    student = service.get_or_create_student_for_user(user)
    milestones = service.list_milestones_for_student(student.id)
    milestone = next((item for item in milestones if item["id"] == milestone_id), None)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return templates.TemplateResponse(
        request=request,
        name="milestone_detail.html",
        context={
            "user": user,
            "milestone": milestone,
        },
    )


@router.get("/app/awards/{award_id}/redeem", response_class=HTMLResponse)
async def redeem_award_detail_view(
    request: Request,
    award_id: int,
    user: AuthDep,
    db: SessionDep,
):
    service = VolunteerService(db)
    student = service.get_or_create_student_for_user(user)
    awards = service.list_awards_for_student(student.id)
    award = next((item for item in awards if item["id"] == award_id), None)
    if award is None:
        raise HTTPException(status_code=404, detail="Award not found")
    if not award["eligible"]:
        raise HTTPException(status_code=403, detail="This award is not yet eligible for redemption")
    if award["redeemed"]:
        raise HTTPException(status_code=409, detail="This award has already been requested")
    return templates.TemplateResponse(
        request=request,
        name="redeem_award.html",
        context={"user": user, "award": award},
    )


@router.post("/app/submissions", response_class=HTMLResponse)
async def create_volunteer_submission(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    activity_name: str = Form(...),
    hours_worked: int = Form(...),
    activity_date: date = Form(...),
    evidence: str = Form(default=""),
    description: str = Form(default=""),
):
    service = VolunteerService(db)
    try:
        service.create_submission_for_user(
            user,
            activity_name=activity_name,
            hours_worked=hours_worked,
            activity_date=activity_date,
            evidence=evidence,
            description=description,
        )
        flash(request, "Volunteer hours submitted for admin review.", "success")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/app/volunteer-hours", response_class=HTMLResponse)
async def submit_volunteer_hours(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    activity_name: str = Form(...),
    hours_worked: int = Form(...),
    activity_date: str = Form(...),
    evidence: str = Form(...),
    description: str = Form(default=""),
):
    # student-build:code-check route
    # Complete a thin service call and redirect; keep persistence out of this route.
    raise NotImplementedError("Complete this workflow snippet")


@router.post("/app/awards/{award_id}/redeem", response_class=HTMLResponse)
async def redeem_award(
    request: Request,
    award_id: int,
    db: SessionDep,
    user: AuthDep,
):
    service = VolunteerService(db)
    try:
        student = service.get_or_create_student_for_user(user)
        service.redeem_award(student.id, award_id)
        flash(request, "Award redemption requested for review.", "success")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("user_awards_view"), status_code=status.HTTP_303_SEE_OTHER)
