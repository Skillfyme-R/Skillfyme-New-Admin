"""
instructors/views.py
---------------------
Views for the Instructor Management module.

HTML views (require login, admin+ role for write ops):
  instructor_list          GET  /instructors/
  instructor_create        GET/POST /instructors/create/
  instructor_edit          GET/POST /instructors/<pk>/edit/
  instructor_delete        POST /instructors/<pk>/delete/
  instructor_payout_report GET  /instructors/report/

JSON API (used by batch creation form JS for auto-fill):
  api_instructor_list      GET  /api/instructors/          → [{id, name, email, cost_per_hour, gst_applicable, gst_percentage, gstin}, ...]
  api_instructor_detail    GET  /api/instructors/<pk>/     → single instructor
  api_batch_cost           GET  /api/batch/<batch_code>/cost/  → cost breakdown
"""

import json
import logging
from datetime import date

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import admin_required, require_role
from core.models import Batch, Cancellation
from instructors.cost_calculator import calculate_batch_cost
from instructors.models import Instructor

logger = logging.getLogger(__name__)


# ── HTML Views ────────────────────────────────────────────────────────────────

def instructor_list(request):
    instructors = Instructor.objects.order_by('name')
    return render(request, 'instructors/instructor_list.html', {'instructors': instructors})


@admin_required
@require_http_methods(['GET', 'POST'])
def instructor_create(request):
    if request.method == 'POST':
        errors = _validate_instructor_form(request.POST)
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            Instructor.objects.create(
                name=request.POST['name'].strip(),
                email=request.POST['email'].strip().lower(),
                phone=request.POST.get('phone', '').strip(),
                cost_per_hour=request.POST['cost_per_hour'],
                gst_applicable=request.POST.get('gst_applicable') == 'on',
                gst_percentage=request.POST.get('gst_percentage') or 18.00,
                gstin=request.POST.get('gstin', '').strip(),
                status=request.POST.get('status', Instructor.Status.ACTIVE),
            )
            messages.success(request, 'Instructor created successfully.')
            logger.info('Instructor created: %s by %s', request.POST['email'], request.user.email)
            return redirect('instructor-list')

    return render(request, 'instructors/instructor_form.html', {
        'action': 'Create',
        'obj': None,
        'status_choices': Instructor.Status.choices,
    })


@admin_required
@require_http_methods(['GET', 'POST'])
def instructor_edit(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)

    if request.method == 'POST':
        errors = _validate_instructor_form(request.POST, exclude_email=instructor.email)
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            instructor.name = request.POST['name'].strip()
            instructor.phone = request.POST.get('phone', '').strip()
            instructor.cost_per_hour = request.POST['cost_per_hour']
            instructor.gst_applicable = request.POST.get('gst_applicable') == 'on'
            instructor.gst_percentage = request.POST.get('gst_percentage') or 18.00
            instructor.gstin = request.POST.get('gstin', '').strip()
            instructor.status = request.POST.get('status', instructor.status)
            instructor.save()
            messages.success(request, 'Instructor updated.')
            logger.info('Instructor updated: %s by %s', instructor.email, request.user.email)
            return redirect('instructor-list')

    return render(request, 'instructors/instructor_form.html', {
        'action': 'Edit',
        'obj': instructor,
        'status_choices': Instructor.Status.choices,
    })


@admin_required
@require_http_methods(['POST'])
def instructor_delete(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    name = instructor.name
    instructor.delete()
    messages.success(request, f'{name} deleted.')
    logger.info('Instructor deleted: %s by %s', name, request.user.email)
    return redirect('instructor-list')


def instructor_payout_report(request):
    """
    Per-instructor payout report: sums billed hours across all assigned batches,
    excluding cancelled sessions.
    """
    today = date.today()
    report_rows = []

    for instructor in Instructor.objects.order_by('name'):
        batches = Batch.objects.filter(instructor_id=instructor.pk)
        total_payout = 0
        batch_details = []

        for batch in batches:
            cancelled_dates = list(
                Cancellation.objects.filter(batch=batch).values_list('cancelled_date', flat=True)
            )
            cost = calculate_batch_cost(
                instructor,
                batch.batch_start_date,
                batch.batch_end_date,
                batch.class_days,
                cancelled_dates,
            )
            total_payout += float(cost['total_cost'])
            batch_details.append({
                'batch_code': batch.batch_code,
                'product_title': batch.product_title,
                'billed_days': cost['billed_days'],
                'total_hours': cost['total_hours'],
                'base_cost': cost['base_cost'],
                'gst_amount': cost['gst_amount'],
                'total_cost': cost['total_cost'],
            })

        report_rows.append({
            'instructor': instructor,
            'batches': batch_details,
            'total_payout': round(total_payout, 2),
        })

    return render(request, 'instructors/payout_report.html', {
        'report_rows': report_rows,
        'generated_at': today,
    })


# ── JSON API ──────────────────────────────────────────────────────────────────

def api_instructor_list(request):
    """Return all active instructors for the batch-form auto-fill dropdown."""
    instructors = Instructor.objects.filter(status=Instructor.Status.ACTIVE).order_by('name')
    data = [_serialize_instructor(i) for i in instructors]
    return JsonResponse(data, safe=False)


def api_instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    return JsonResponse(_serialize_instructor(instructor))


def api_batch_cost(request, batch_code):
    """
    Calculate and return cost breakdown for a batch.
    Uses the instructor assigned to the batch (if any).
    """
    try:
        batch = Batch.objects.get(batch_code=batch_code)
    except Batch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)

    if not getattr(batch, 'instructor_id', None):
        return JsonResponse({'error': 'No instructor assigned to this batch'}, status=400)

    try:
        instructor = Instructor.objects.get(pk=batch.instructor_id)
    except Instructor.DoesNotExist:
        return JsonResponse({'error': 'Instructor not found'}, status=404)

    cancelled_dates = list(
        Cancellation.objects.filter(batch=batch).values_list('cancelled_date', flat=True)
    )
    cost = calculate_batch_cost(
        instructor,
        batch.batch_start_date,
        batch.batch_end_date,
        batch.class_days,
        cancelled_dates,
    )
    return JsonResponse({k: str(v) if hasattr(v, 'quantize') else v for k, v in cost.items()})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_instructor(instructor):
    return {
        'id': instructor.pk,
        'name': instructor.name,
        'email': instructor.email,
        'phone': instructor.phone,
        'cost_per_hour': str(instructor.cost_per_hour),
        'gst_applicable': instructor.gst_applicable,
        'gst_percentage': str(instructor.gst_percentage),
        'gstin': instructor.gstin,
        'status': instructor.status,
    }


def _validate_instructor_form(data, exclude_email=None):
    errors = []
    if not data.get('name', '').strip():
        errors.append('Name is required.')
    email = data.get('email', '').strip().lower()
    if not email:
        errors.append('Email is required.')
    elif exclude_email is None:  # only check uniqueness on create
        if Instructor.objects.filter(email=email).exists():
            errors.append(f'An instructor with email {email} already exists.')
    if not data.get('cost_per_hour', '').strip():
        errors.append('Cost per hour is required.')
    else:
        try:
            float(data['cost_per_hour'])
        except ValueError:
            errors.append('Cost per hour must be a number.')
    return errors