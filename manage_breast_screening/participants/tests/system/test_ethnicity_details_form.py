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


class TestEthnicityDetailsForm(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        self.participant = ParticipantFactory(ethnic_background_id="")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)

    def test_entering_ethnicity_details_for_a_participant(self):
        self.given_i_am_viewing_an_appointment()
        self.when_i_click_on_enter_ethnicity_details()
        self.then_i_should_be_on_the_ethnicity_details_form()

        self.when_i_submit_the_form()
        self.then_i_see_an_error()

        self.when_i_select_an_ethnicity()
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_ethnicity_is_updated()

        self.when_i_click_the_change_ethnicity_link()
        self.then_i_should_be_on_the_ethnicity_details_form()
        self.when_i_choose_a_non_specific_ethnicity()
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_new_ethnicity_is_recorded()

    def given_i_am_viewing_an_appointment(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:start_screening",
                kwargs={"id": self.appointment.pk},
            )
        )

    def when_i_click_on_enter_ethnicity_details(self):
        self.page.get_by_role("link", name="Enter ethnicity details").click()

    def then_i_should_be_on_the_ethnicity_details_form(self):
        expect(self.page).to_have_url(
            re.compile(
                reverse(
                    "participants:edit_ethnicity",
                    kwargs={"id": self.participant.id},
                )
            )
        )

    def when_i_submit_the_form(self):
        self.page.get_by_role("button", name="Save and continue").click()

    def then_i_see_an_error(self):
        error_summary = self.page.locator(".nhsuk-error-summary")
        expect(error_summary).to_contain_text("Select an ethnic background")
        inline_error = self.page.locator("span.nhsuk-error-message")
        expect(inline_error).to_contain_text("Select an ethnic background")

    def when_i_select_an_ethnicity(self):
        self.page.get_by_label("Chinese").check()

    def and_i_submit_the_form(self):
        self.page.get_by_role("button", name="Save and continue").click()

    def then_i_should_be_back_on_the_appointment(self):
        expect(self.page).to_have_url(
            re.compile(
                reverse(
                    "mammograms:start_screening",
                    kwargs={"id": self.appointment.pk},
                )
            )
        )

    def and_the_ethnicity_is_updated(self):
        ethnicity_row = self.page.locator(".nhsuk-summary-list__row").filter(
            has_text="Ethnicity"
        )
        expect(ethnicity_row).to_contain_text("Asian or Asian British (Chinese)")
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.ethnic_background_id, "chinese")

    def when_i_click_the_change_ethnicity_link(self):
        self.page.get_by_role("link", name="Change ethnicity").click()

    def when_i_choose_a_non_specific_ethnicity(self):
        self.page.get_by_label("Any other White background").check()

    def and_the_new_ethnicity_is_recorded(self):
        self.participant.refresh_from_db()
        self.assertEqual(
            self.participant.ethnic_background_id, "any_other_white_background"
        )
        ethnicity_row = self.page.locator(".nhsuk-summary-list__row").filter(
            has_text="Ethnicity"
        )
        expect(ethnicity_row).to_contain_text("White (Any other White background)")
