from logging import getLogger

from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .forms import EthnicityForm
from .models import Participant
from .presenters import ParticipantPresenter

logger = getLogger(__name__)


def show(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    presenter = ParticipantPresenter(participant)

    return render(
        request,
        "participants/show.jinja",
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
                "href": request.GET.get("return_url"),
            },
        },
    )
