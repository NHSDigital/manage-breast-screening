from logging import getLogger

from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Appointment, Participant
from .presenters import ParticipantAppointmentsPresenter, ParticipantPresenter

logger = getLogger(__name__)


def show(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    presented_participant = ParticipantPresenter(participant)

    appointments = (
        Appointment.objects.select_related("clinic_slot__clinic__setting")
        .filter(screening_episode__participant=participant)
        .order_by("-clinic_slot__starts_at")
    )

    presented_appointments = ParticipantAppointmentsPresenter(
        past_appointments=list(appointments.past()),
        upcoming_appointments=list(appointments.upcoming()),
    )

    return render(
        request,
        "participants/show.jinja",
        context={
            "presented_participant": presented_participant,
            "presented_appointments": presented_appointments,
            "heading": participant.full_name,
            "back_link": {
                "text": "Back to participants",
                "href": reverse("participants:index"),
            },
        },
    )
