from django.urls import reverse

from ..core.utils.date_formatting import format_date, format_relative_date
from ..core.utils.string_formatting import (
    format_age,
    format_nhs_number,
    format_phone_number,
    sentence_case,
)


class ParticipantPresenter:
    def __init__(self, participant):
        self._participant = participant

        self.id = participant.id
        self.extra_needs = participant.extra_needs
        # self.ethnic_group = participant.ethnic_group
        self.full_name = participant.full_name
        self.gender = participant.gender
        self.email = participant.email
        self.phone = format_phone_number(participant.phone)
        self.nhs_number = format_nhs_number(participant.nhs_number)
        self.date_of_birth = format_date(participant.date_of_birth)
        self.age = format_age(participant.age())
        self.risk_level = sentence_case(participant.risk_level)
        self.url = reverse("participants:show", kwargs={"id": participant.id})

    @property
    def ethnic_group_category(self):
        category = self._participant.ethnic_group_category()
        if category:
            return category.replace("Any other", "any other")
        else:
            return None

    @property
    def address(self):
        address = self._participant.address
        if not address:
            return {}

        return {"lines": address.lines, "postcode": address.postcode}


class ScreeningHistoryPresenter:
    def __init__(self, screening_episodes):
        self._episodes = list(screening_episodes)
        self._last_known_screening = screening_episodes[1]

    @property
    def last_known_screening(self):
        return (
            {
                "date": format_date(self._last_known_screening.created_at),
                "relative_date": format_relative_date(
                    self._last_known_screening.created_at
                ),
                # TODO: the current model doesn't allow for knowing the type and location of a historical screening
                # if it is not tied to one of our clinic slots.
                "location": None,
                "type": None,
            }
            if self._last_known_screening
            else {}
        )
