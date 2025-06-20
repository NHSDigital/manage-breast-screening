from logging import getLogger

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .models import Participant
from .presenters import ParticipantPresenter
from .forms import EthnicityForm

logger = getLogger(__name__)


def show(request, id):
    participant = get_object_or_404(Participant, id=id)
    presenter = ParticipantPresenter(participant)

    return render(
        request,
        "show.jinja",
        context={
            "participant": presenter,
            "heading": participant.full_name,
            "back_link": {
                "text": "Back to participants",
                "href": reverse("participants:index"),
            },
        },
    )


def edit_ethnicity(request, id):
    participant = get_object_or_404(Participant, id=id)

    if request.method == "POST":
        form = EthnicityForm(request.POST, participant=participant)
        if form.is_valid():
            form.save()
            return redirect("participants:show", kwargs={"id": participant.id})
    else:
        form = EthnicityForm(participant=participant)

    return render(
        request,
        "edit_ethnicity.jinja",
        context={
            "participant": participant,
            "form": form,
            "heading": "Ethnicity",
            "back_link": {
                "text": "Go back",
                "href": reverse("participants:show", kwargs={"id": participant.id}),
            },
        },
    )
