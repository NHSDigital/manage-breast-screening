from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from manage_breast_screening.participants.presenters import (
    ParticipantAppointmentsPresenter,
    ParticipantPresenter,
)

from ..models import Appointment, AppointmentStatus, Participant


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
    def test_ethnic_group_category(self, mock_participant, category, formatted):
        mock_participant.ethnic_group_category.return_value = category
        result = ParticipantPresenter(mock_participant)
        assert result.ethnic_group_category == formatted

    def test_presented_values(self, mock_participant):
        mock_participant.extra_needs = None
        mock_participant.ethnic_group = "Irish"
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
        assert result.ethnic_group == "Irish"
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


class TestParticipantAppointmentPresenter:
    def mock_appointment(self, starts_at, pk, state=AppointmentStatus.CONFIRMED):
        appointment = MagicMock(spec=Appointment)
        appointment.clinic_slot.starts_at = starts_at
        appointment.clinic_slot.clinic.get_type_display.return_value = "screening"
        appointment.clinic_slot.clinic.setting.name = "West of London BSS"
        appointment.pk = UUID(pk)
        appointment.current_status = AppointmentStatus(state=state)

        return appointment

    @pytest.fixture
    def upcoming_appointments(self):
        return [
            self.mock_appointment(
                starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc),
                pk="e3d475a6-c405-44d6-bbd7-bcb5cd4d4996",
            )
        ]

    @pytest.fixture
    def past_appointments(self):
        return [
            self.mock_appointment(
                starts_at=datetime(2023, 1, 1, 9, tzinfo=tz.utc),
                pk="e76163c8-a594-4991-890d-a02097c67a2f",
                state=AppointmentStatus.PARTIALLY_SCREENED,
            ),
            self.mock_appointment(
                starts_at=datetime(2019, 1, 1, 9, tzinfo=tz.utc),
                pk="6473a629-e7c4-43ca-87f3-ab9526aab07c",
                state=AppointmentStatus.SCREENED,
            ),
        ]

    def test_upcoming(self, upcoming_appointments, past_appointments, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, 9, tzinfo=tz.utc))

        presenter = ParticipantAppointmentsPresenter(
            past_appointments=past_appointments,
            upcoming_appointments=upcoming_appointments,
        )
        assert presenter.upcoming == [
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2025",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--blue app-nowrap",
                    "key": "CONFIRMED",
                    "text": "Confirmed",
                },
                "/mammograms/e3d475a6-c405-44d6-bbd7-bcb5cd4d4996/start-screening/",
            )
        ]

    def test_past(self, upcoming_appointments, past_appointments, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, 9, tzinfo=tz.utc))

        presenter = ParticipantAppointmentsPresenter(
            past_appointments=past_appointments,
            upcoming_appointments=upcoming_appointments,
        )
        assert presenter.past == [
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2023",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--orange app-nowrap",
                    "key": "PARTIALLY_SCREENED",
                    "text": "Partially screened",
                },
                "/mammograms/e76163c8-a594-4991-890d-a02097c67a2f/start-screening/",
            ),
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2019",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--green app-nowrap",
                    "key": "SCREENED",
                    "text": "Screened",
                },
                "/mammograms/6473a629-e7c4-43ca-87f3-ab9526aab07c/start-screening/",
            ),
        ]
