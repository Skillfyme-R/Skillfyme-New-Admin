"""
instructors/models.py
----------------------
Instructor model — standalone table, no changes to existing models.

The Batch model is extended (new FK + cost columns) via a separate migration
(instructors/migrations/0002_batch_instructor_fk.py) that only ADDS columns.
This file defines only the new Instructor table.
"""

from django.db import models


class Instructor(models.Model):
    """
    Stores instructor details used in batch assignments and cost calculations.
    Only Active instructors are shown in the batch creation dropdown.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    name = models.CharField(max_length=300)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    gst_applicable = models.BooleanField(default=False)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    gstin = models.CharField(max_length=15, blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instructors'
        ordering = ['name']

    def __str__(self):
        return f'<Instructor {self.name!r} ({self.email})>'