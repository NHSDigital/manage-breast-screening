import uuid
from datetime import date

from django.contrib.postgres.fields import ArrayField
from django.db import models

from ..core.models import BaseModel

# List of ethnic groups from
# https://design-system.service.gov.uk/patterns/equality-information/
# This list is specific to England.


class Ethnicity(models.Model):
    # fmt: off
    DATA = {
        "White": [
            { "id": "english_welsh_scottish_ni_british", "display_name": "English, Welsh, Scottish, Northern Irish or British", },
            { "id": "irish", "display_name": "Irish" },
            { "id": "gypsy_or_irish_traveller", "display_name": "Gypsy or Irish Traveller" },
            { "id": "any_other_white_background", "display_name": "Any other White background" },
        ],
        "Mixed or multiple ethnic groups": [
            { "id": "white_and_black_caribbean", "display_name": "White and Black Caribbean" },
            { "id": "white_and_black_african", "display_name": "White and Black African" },
            { "id": "white_and_asian", "display_name": "White and Asian" },
            { "id": "any_other_mixed_or_multiple_ethnic_background", "display_name": "Any other mixed or multiple ethnic background" },
        ],
        "Asian or Asian British": [
            { "id": "indian", "display_name": "Indian" },
            { "id": "pakistani", "display_name": "Pakistani" },
            { "id": "bangladeshi", "display_name": "Bangladeshi" },
            { "id": "chinese", "display_name": "Chinese" },
            { "id": "any_other_asian_background", "display_name": "Any other Asian background" },
        ],
        "Black, African, Caribbean or Black British": [
            { "id": "african", "display_name": "African" },
            { "id": "caribbean", "display_name": "Caribbean" },
            { "id": "any_other_black_african_or_caribbean_background", "display_name": "Any other Black, African or Caribbean background" },
        ],
        "Other ethnic group": [
            { "id": "arab", "display_name": "Arab" },
            { "id": "any_other_ethnic_group", "display_name": "Any other ethnic group" },
            { "id": "prefer_not_to_say", "display_name": "Prefer not to say" },
        ],
    }
    # fmt: on

    @classmethod
    def ethnic_groups_with_display_names(cls):
        choices = []
        for _ethnic_category, ethnic_groups in cls.DATA.items():
            for ethnic_group in ethnic_groups:
                choices.append((ethnic_group["id"], ethnic_group["display_name"]))
        return tuple(choices)

    @classmethod
    def non_specific_ethnic_groups(cls):
        return [
            "any_other_white_background",
            "any_other_mixed_or_multiple_ethnic_background",
            "any_other_asian_background",
            "any_other_black_african_or_caribbean_background",
            "any_other_ethnic_group",
        ]


class Participant(BaseModel):
    PREFER_NOT_TO_SAY = "Prefer not to say"
    # ETHNIC_GROUP_CHOICES = [
    #     (group, group) for groups in ETHNIC_GROUPS.values() for group in groups
    # ] + [(PREFER_NOT_TO_SAY, PREFER_NOT_TO_SAY)]

    first_name = models.TextField()
    last_name = models.TextField()
    gender = models.TextField()
    nhs_number = models.TextField()
    phone = models.TextField()
    email = models.EmailField()
    date_of_birth = models.DateField()
    # ethnic_group = models.CharField(blank=True, null=True, choices=ETHNIC_GROUP_CHOICES)
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

    # def ethnic_group_category(self):
    #     matches = [
    #         category
    #         for category, groups in EthnicGroup.DATA.items()
    #         if self.ethnic_group in groups
    #     ]
    #     return matches[0] if matches else None


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
    def remaining(self):
        return self.filter(
            status__in=[
                Appointment.Status.CONFIRMED,
                Appointment.Status.CHECKED_IN,
            ]
        )

    def checked_in(self):
        return self.filter(status=Appointment.Status.CHECKED_IN)

    def complete(self):
        return self.filter(
            status__in=[
                Appointment.Status.CANCELLED,
                Appointment.Status.DID_NOT_ATTEND,
                Appointment.Status.SCREENED,
                Appointment.Status.PARTIALLY_SCREENED,
                Appointment.Status.ATTENDED_NOT_SCREENED,
            ]
        )

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
    class Status:
        CONFIRMED = "CONFIRMED"
        CANCELLED = "CANCELLED"
        DID_NOT_ATTEND = "DID_NOT_ATTEND"
        CHECKED_IN = "CHECKED_IN"
        SCREENED = "SCREENED"
        PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
        ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        Status.CONFIRMED: "Confirmed",
        Status.CANCELLED: "Cancelled",
        Status.DID_NOT_ATTEND: "Did not attend",
        Status.CHECKED_IN: "Checked in",
        Status.SCREENED: "Screened",
        Status.PARTIALLY_SCREENED: "Partially screened",
        Status.ATTENDED_NOT_SCREENED: "Attended not screened",
    }

    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=50, default=Status.CONFIRMED
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)
