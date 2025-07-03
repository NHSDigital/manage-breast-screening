import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from ..participants.models import Appointment, AppointmentStatus, Participant
from .forms import (
    AppointmentCannotGoAheadForm,
    AskForMedicalInformationForm,
    RecordMedicalInformationForm,
    ScreeningAppointmentForm,
)
from .presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    present_secondary_nav,
)

APPOINTMENT_CANNOT_PROCEED = "Appointment cannot proceed"

logger = logging.getLogger(__name__)


class BaseAppointmentForm(FormView):
    @property
    def appointment_id(self):
        return self.kwargs["id"]

    def get_appointment(self):
        return get_object_or_404(
            Appointment.objects.prefetch_related(
                "clinic_slot",
                "screening_episode__participant",
                "screening_episode__participant__address",
            ),
            pk=self.appointment_id,
        )


class StartScreening(BaseAppointmentForm):
    template_name = "mammograms/start_screening.jinja"
    form_class = ScreeningAppointmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        appointment = self.get_appointment()
        last_known_screening = appointment.screening_episode.previous()
        appointment_presenter = AppointmentPresenter(appointment)
        last_known_mammogram_presenter = LastKnownMammogramPresenter(
            last_known_screening,
            participant_pk=appointment.screening_episode.participant.pk,
        )

        context.update(
            {
                "title": appointment_presenter.participant.full_name,
                "caption": f"{appointment_presenter.clinic_slot.clinic_type} appointment",
                "presented_appointment": appointment_presenter,
                "presented_participant": appointment_presenter.participant,
                "presented_mammograms": last_known_mammogram_presenter,
                "decision_legend": "Can the appointment go ahead?",
                "decision_hint": "Before you proceed, check the participant’s identity and confirm that their last mammogram was more than 6 months ago.",
            }
        )

        if AppointmentStatus in [
            AppointmentStatus.SCREENED,
            AppointmentStatus.PARTIALLY_SCREENED,
        ]:
            context["secondary_nav_items"] = present_secondary_nav(appointment.pk)

        return context

    def form_valid(self, form):
        form.save()

        if form.cleaned_data["decision"] == "continue":
            return redirect(
                "mammograms:ask_for_medical_information",
                id=self.get_appointment().pk,
            )
        else:
            return redirect(
                "mammograms:appointment_cannot_go_ahead",
                id=self.get_appointment().pk,
            )


class AskForMedicalInformation(BaseAppointmentForm):
    template_name = "mammograms/ask_for_medical_information.jinja"
    form_class = AskForMedicalInformationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs["id"]
        participant = Participant.objects.get(screeningepisode__appointment__id=id)

        context.update(
            {
                "participant": participant,
                "caption": participant.full_name,
                "title": "Medical information",
                "decision_legend": "Has the participant shared any relevant medical information?",
                "cannot_continue_link": {
                    "href": reverse(
                        "mammograms:appointment_cannot_go_ahead",
                        kwargs={"id": id},
                    ),
                    "text": APPOINTMENT_CANNOT_PROCEED,
                },
            }
        )

        return context

    def form_valid(self, form):
        form.save()

        appointment = self.get_appointment()

        if form.cleaned_data["decision"] == "yes":
            return redirect("mammograms:record_medical_information", id=appointment.pk)
        else:
            return redirect("mammograms:awaiting_images", id=appointment.pk)


class RecordMedicalInformation(BaseAppointmentForm):
    template_name = "mammograms/record_medical_information.jinja"
    form_class = RecordMedicalInformationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs["id"]
        participant = get_object_or_404(
            Participant, screeningepisode__appointment__id=id
        )
        context.update(
            {
                "title": "Record medical information",
                "participant": participant,
                "caption": participant.full_name,
                "decision_legend": "Can imaging go ahead?",
            }
        )
        return context

    def form_valid(self, form):
        form.save()

        appointment = self.get_appointment()

        if form.cleaned_data["decision"] == "continue":
            return redirect("mammograms:awaiting_images", id=appointment.pk)
        else:
            return redirect("mammograms:appointment_cannot_go_ahead", id=appointment.pk)


def appointment_cannot_go_ahead(request, id):
    appointment = get_object_or_404(Appointment, pk=id)
    participant = appointment.screening_episode.participant

    if request.method == "POST":
        form = AppointmentCannotGoAheadForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect("clinics:index")
    else:
        form = AppointmentCannotGoAheadForm(instance=appointment)

    return render(
        request,
        "mammograms/appointment_cannot_go_ahead.jinja",
        {
            "title": "Appointment cannot go ahead",
            "caption": participant.full_name,
            "form": form,
            "decision_legend": "Does the appointment need to be rescheduled?",
        },
    )


def awaiting_images(request, id):
    return render(
        request,
        "mammograms/awaiting_images.jinja",
        {"title": "Awaiting images"},
    )


@require_http_methods(["POST"])
def check_in(_request, id):
    appointment = get_object_or_404(Appointment, pk=id)
    appointment.statuses.create(state=AppointmentStatus.CHECKED_IN)

    return redirect("mammograms:start_screening", id=id)
