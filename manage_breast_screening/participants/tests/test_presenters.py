from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from manage_breast_screening.participants.presenters import ParticipantPresenter

from ..models import Participant


class TestParticipantPresenter:
    @pytest.fixture(autouse=True)
    def set_time(self, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, tzinfo=tz.utc))

    @pytest.fixture
    def mock_participant(self):
        mock = MagicMock(spec=Participant)
        mock.nhs_number = "99900900829"
        mock.pk = uuid4()
        return mock

    @pytest.mark.parametrize(
        "category, formatted",
        [
            (
                "Black, African, Caribbean or Black British",
                "Black, African, Caribbean or Black British",
            ),
            (None, None),
            ("Any other", "any other"),
        ],
    )
    def test_ethnic_background_category(self, mock_participant, category, formatted):
        mock_participant.ethnic_background_category.return_value = category
        result = ParticipantPresenter(mock_participant)
        assert result.ethnic_background_category == formatted

    def test_presented_values(self, mock_participant):
        mock_participant.extra_needs = None
        mock_participant.ethnic_background = "Irish"
        mock_participant.full_name = "Firstname Lastname"
        mock_participant.gender = "Female"
        mock_participant.email = "Firstname.Lastname@example.com"
        mock_participant.address.lines = ["1", "2", "3"]
        mock_participant.address.postcode = ["A123 "]
        mock_participant.phone = "07700 900000"
        mock_participant.date_of_birth = date(1955, 1, 1)
        mock_participant.age.return_value = 70
        mock_participant.risk_level = None

        result = ParticipantPresenter(mock_participant)

        assert result.extra_needs is None
        assert result.ethnic_background == "Irish"
        assert result.full_name == "Firstname Lastname"
        assert result.gender == "Female"
        assert result.email == "Firstname.Lastname@example.com"
        assert result.address == {"lines": ["1", "2", "3"], "postcode": ["A123 "]}
        assert result.phone == "07700 900000"
        assert result.nhs_number == "999 009 00829"
        assert result.date_of_birth == "1 January 1955"
        assert result.age == "70 years old"
        assert result.risk_level == ""
        assert result.url == f"/participants/{mock_participant.pk}/"
