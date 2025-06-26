import pytest

from manage_breast_screening.core.system_test_setup import SystemTestCase
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


class TestEthnicityDetailsForm(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        self.participant = ParticipantFactory(ethnic_background="")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)

    @pytest.mark.skip("Not implemented")
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
