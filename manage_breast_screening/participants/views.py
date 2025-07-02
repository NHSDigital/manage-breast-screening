from logging import getLogger

from django.db.models import Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..clinics.models import Provider
from .forms import EthnicityForm, ParticipantRecordedMammogramForm
from .models import Appointment, Participant
from .presenters import ParticipantAppointmentsPresenter, ParticipantPresenter

logger = getLogger(__name__)


def show(request, id):
    participant = get_object_or_404(Participant, pk=id)
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


def edit_ethnicity(request, id):
    participant = get_object_or_404(Participant, pk=id)

    if request.method == "POST":
        return_url = request.POST.get("return_url")
        form = EthnicityForm(request.POST, participant=participant)
        if form.is_valid():
            form.save()
            return redirect(return_url)
    else:
        return_url = request.GET.get("return_url")
        form = EthnicityForm(participant=participant)

    return_url = return_url or reverse(
        "participants:show", kwargs={"id": participant.pk}
    )

    return render(
        request,
        "edit_ethnicity.jinja",
        context={
            "participant": participant,
            "form": form,
            "heading": "Ethnicity",
            "back_link": {
                "text": "Go back",
                "href": return_url,
            },
        },
    )


def add_previous_mammogram(request, pk):
    participant = get_object_or_404(Participant, pk=pk)

    # TODO: extract to method. ensure this exists?
    current_provider_id = Subquery(
        Appointment.objects.select_related("clinic_slot__clinic__setting__provider")
        .filter(
            screening_episode__participant_id=pk,
        )
        .order_by("-clinic_slot__starts_at")
        .values("clinic_slot__clinic__setting__provider_id")[:1]
    )

    current_provider = Provider.objects.get(pk=current_provider_id)

    if request.method == "POST":
        form = ParticipantRecordedMammogramForm(
            data=request.POST,
            participant=participant,
            current_provider=current_provider,
        )
        if form.is_valid():
            form.save()
            return redirect("clinics:index")
    else:
        form = ParticipantRecordedMammogramForm(
            participant=participant, current_provider=current_provider
        )

    return render(
        request,
        "participants/add_previous_mammogram.jinja",
        {
            "title": "Add details of a previous mammogram",
            "caption": participant.full_name,
            "form": form,
            "back_link_params": {
                "href": reverse("participants:show", kwargs={"pk": pk}),
                "text": "Go back",
            },
        },
    )
