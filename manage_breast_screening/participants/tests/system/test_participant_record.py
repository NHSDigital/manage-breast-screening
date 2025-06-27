import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.system_test_setup import SystemTestCase
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


class TestParticipantRecord(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)

    @pytest.mark.skip("not implemented yet")
    def test_viewing_participant_record_from_an_appointment(self):
        self.given_i_am_viewing_an_appointment()
        self.when_i_click_on_view_participant_record()
        self.then_i_should_be_on_the_participant_record_page()
        self.and_i_should_see_the_participant_record()
        self.when_i_click_on_the_back_link()
        self.then_i_should_be_back_on_the_appointment()

    def test_accessibility(self):
        self.given_i_am_on_the_participant_record_page()
        self.then_the_accessibility_baseline_is_met()

    def given_i_am_viewing_an_appointment(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:start_screening",
                kwargs={"id": self.appointment.pk},
            )
        )

    def given_i_am_on_the_participant_record_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "participants:show",
                kwargs={"id": self.participant.pk},
            )
        )

    def when_i_click_on_view_participant_record(self):
        self.page.get_by_text("View participant record").click()

    def then_i_should_be_on_the_participant_record_page(self):
        path = reverse(
            "participants:show",
            kwargs={"id": self.participant.pk},
        )
        expect(self.page).to_have_url(re.compile(path))

    def and_i_should_see_the_participant_record(self):
        main = self.page.get_by_role("main")
        expect(main).to_contain_text("Janet Williams")
        expect(main).to_contain_text("Personal details")

    def when_i_click_on_the_back_link(self):
        self.page.get_by_text("Back to appointment").click()

    def then_i_should_be_back_on_the_appointment(self):
        path = reverse(
            "mammograms:start_screening",
            kwargs={"id": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
