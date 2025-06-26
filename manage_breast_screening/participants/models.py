import uuid
from datetime import date
from logging import getLogger

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import OuterRef, Subquery

from ..core.models import BaseModel

logger = getLogger(__name__)

# List of ethnic groups from
# https://design-system.service.gov.uk/patterns/equality-information/
# This list is specific to England.
ETHNIC_GROUPS = {
    "White": [
        "English, Welsh, Scottish, Northern Irish or British",
        "Irish",
        "Gypsy or Irish Traveller",
        "Any other White background",
    ],
    "Mixed or multiple ethnic groups": [
        "White and Black Caribbean",
        "White and Black African",
        "White and Asian",
        "Any other mixed or multiple ethnic background",
    ],
    "Asian or Asian British": [
        "Indian",
        "Pakistani",
        "Bangladeshi",
        "Chinese",
        "Any other Asian background",
    ],
    "Black, African, Caribbean or Black British": [
        "African",
        "Caribbean",
        "Any other Black, African or Caribbean background",
    ],
    "Other ethnic group": ["Arab", "Any other ethnic group"],
}


class Participant(BaseModel):
    PREFER_NOT_TO_SAY = "Prefer not to say"
    ETHNIC_GROUP_CHOICES = [
        (group, group) for groups in ETHNIC_GROUPS.values() for group in groups
    ] + [(PREFER_NOT_TO_SAY, PREFER_NOT_TO_SAY)]

    first_name = models.TextField()
    last_name = models.TextField()
    gender = models.TextField()
    nhs_number = models.TextField()
    phone = models.TextField()
    email = models.EmailField()
    date_of_birth = models.DateField()
    ethnic_group = models.CharField(blank=True, null=True, choices=ETHNIC_GROUP_CHOICES)
    risk_level = models.TextField()
    extra_needs = models.JSONField(null=False, default=list, blank=True)

    @property
    def full_name(self):
        return " ".join([name for name in [self.first_name, self.last_name] if name])

    def age(self):
        today = date.today()
        if (today.month, today.day) >= (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
            return today.year - self.date_of_birth.year
        else:
            return today.year - self.date_of_birth.year - 1

    def ethnic_group_category(self):
        matches = [
            category
            for category, groups in ETHNIC_GROUPS.items()
            if self.ethnic_group in groups
        ]
        return matches[0] if matches else None


class ParticipantAddress(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    participant = models.OneToOneField(
        Participant, on_delete=models.PROTECT, related_name="address"
    )
    lines = ArrayField(models.CharField(), size=5, blank=True)
    postcode = models.CharField(blank=True, null=True)


class ScreeningEpisode(BaseModel):
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)

    def screening_history(self):
        """
        Return all previous screening episodes, excluding this one, prefetching
        their appointment details as well.
        """
        return (
            ScreeningEpisode.objects.prefetch_related(
                "appointment_set__clinic_slot__clinic__setting__provider"
            )
            .filter(participant__pk=self.participant.pk)
            .exclude(pk=self.pk)
            .order_by("-created_at")
        )

    def previous(self) -> "ScreeningEpisode | None":
        """
        Return the last known screening episode
        """
        try:
            return self.screening_history()[0]
        except IndexError:
            return None


class AppointmentQuerySet(models.QuerySet):
    def in_status(self, *statuses):
        return self.filter(
            statuses=Subquery(
                AppointmentStatus.objects.filter(
                    appointment=OuterRef("pk"),
                    state__in=statuses,
                )
                .values("pk")
                .order_by("-created_at")[:1]
            )
        )

    def remaining(self):
        return self.in_status(
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
        )

    def checked_in(self):
        return self.in_status(AppointmentStatus.CHECKED_IN)

    def complete(self):
        return self.in_status(
            AppointmentStatus.CANCELLED,
            AppointmentStatus.DID_NOT_ATTEND,
            AppointmentStatus.SCREENED,
            AppointmentStatus.PARTIALLY_SCREENED,
            AppointmentStatus.ATTENDED_NOT_SCREENED,
        )

    def upcoming(self):
        return self.filter(clinic_slot__starts_at__gte=date.today())

    def past(self):
        return self.filter(clinic_slot__starts_at__lt=date.today())

    def for_clinic_and_filter(self, clinic, filter):
        match filter:
            case "remaining":
                return self.remaining().filter(clinic_slot__clinic=clinic)
            case "checked_in":
                return self.checked_in().filter(clinic_slot__clinic=clinic)
            case "complete":
                return self.complete().filter(clinic_slot__clinic=clinic)
            case "all":
                return self.filter(clinic_slot__clinic=clinic)
            case _:
                raise ValueError(filter)

    def filter_counts_for_clinic(self, clinic):
        counts = {}
        for filter in ["remaining", "checked_in", "complete", "all"]:
            counts[filter] = self.for_clinic_and_filter(clinic, filter).count()
        return counts


class Appointment(BaseModel):
    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)

    @property
    def current_status(self) -> "AppointmentStatus":
        """
        Fetch the most recent status associated with this appointment.
        If there are no statuses for any reason, assume the default one.
        """
        # avoid `first()` here so that `statuses` can be prefetched
        # when fetching many appointments
        statuses = list(self.statuses.order_by("-created_at").all())

        if not statuses:
            status = AppointmentStatus()
            logger.info(
                f"Appointment {self.pk} has no statuses. Assuming {status.state}"
            )
            return status

        return statuses[0]


class AppointmentStatus(models.Model):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DID_NOT_ATTEND = "DID_NOT_ATTEND"
    CHECKED_IN = "CHECKED_IN"
    SCREENED = "SCREENED"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        CONFIRMED: "Confirmed",
        CANCELLED: "Cancelled",
        DID_NOT_ATTEND: "Did not attend",
        CHECKED_IN: "Checked in",
        SCREENED: "Screened",
        PARTIALLY_SCREENED: "Partially screened",
        ATTENDED_NOT_SCREENED: "Attended not screened",
    }
    state = models.CharField(choices=STATUS_CHOICES, max_length=50, default=CONFIRMED)

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        Appointment, on_delete=models.PROTECT, related_name="statuses"
    )

    class Meta:
        ordering = ["-created_at"]
