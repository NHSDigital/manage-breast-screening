from datetime import date, datetime
from datetime import timezone as tz
from uuid import uuid4

import pytest

from manage_breast_screening.participants.presenters import ParticipantPresenter

from .factories import ParticipantAddressFactory, ParticipantFactory


class TestParticipantPresenter:
    @pytest.fixture(autouse=True)
    def set_time(self, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, tzinfo=tz.utc))

    @pytest.fixture
    def participant(self):
        participant_id = uuid4()
        participant = ParticipantFactory.build(
            id=participant_id,
            nhs_number="99900900829",
            ethnic_background_id="irish",
            first_name="Firstname",
            last_name="Lastname",
            gender="Female",
            email="Firstname.Lastname@example.com",
            phone="07700 900000",
            date_of_birth=date(1955, 1, 1),
            risk_level=None,
            extra_needs=None,
        )
        participant.address = ParticipantAddressFactory.build(
            participant=participant, lines=["1", "2", "3"], postcode="A123 "
        )

        return participant

    def test_presented_values(self, participant):
        result = ParticipantPresenter(participant)

        assert result.extra_needs is None
        assert result.ethnic_background == "Irish"
        assert result.ethnic_category == "White"
        assert result.full_name == "Firstname Lastname"
        assert result.gender == "Female"
        assert result.email == "Firstname.Lastname@example.com"
        assert result.address == {"lines": ["1", "2", "3"], "postcode": "A123 "}
        assert result.phone == "07700 900000"
        assert result.nhs_number == "999 009 00829"
        assert result.date_of_birth == "1 January 1955"
        assert result.age == "70 years old"
        assert result.risk_level == ""
        assert result.url == f"/participants/{participant.id}/"
