from enum import StrEnum

from django import forms
from django.forms import ChoiceField, ModelForm, ValidationError

from .models import Ethnicity, ParticipantReportedMammogram


class EthnicityForm(forms.Form):
    ethnic_background_choice = forms.ChoiceField(
        choices=Ethnicity.ethnic_background_ids_with_display_names(),
        required=True,
        error_messages={"required": "Select an ethnic background"},
    )

    def __init__(self, *args, **kwargs):
        if "participant" not in kwargs:
            raise ValueError("EthnicityForm requires a participant")
        self.participant = kwargs.pop("participant")

        # Set initial value for ethnic_background_choice from participant
        initial = kwargs.get("initial", {})
        initial["ethnic_background_choice"] = self.participant.ethnic_background_id
        kwargs["initial"] = initial

        super().__init__(*args, **kwargs)

        for ethnic_background in self.non_specific_ethnic_backgrounds():
            self.fields[ethnic_background + "_details"] = forms.CharField(
                required=False
            )

    def ethnic_backgrounds_by_category(self):
        return Ethnicity.DATA.items()

    def non_specific_ethnic_backgrounds(self):
        return Ethnicity.non_specific_ethnic_backgrounds()

    def save(self):
        self.participant.ethnic_background_id = self.cleaned_data[
            "ethnic_background_choice"
        ]
        self.participant.save()


class ParticipantRecordedMammogramForm(ModelForm):
    class Meta:
        model = ParticipantReportedMammogram
        fields = [
            "provider",
            "location_details",
            "exact_date",
            "approx_date",
            "different_name",
            "additional_information",
        ]

    class WhereTaken(StrEnum):
        SAME_UNIT = "same_unit"
        ANOTHER_UNIT = "another_unit"
        ELSEWHERE_UK = ParticipantReportedMammogram.LocationType.ELSEWHERE_UK.value
        OUTSIDE_UK = ParticipantReportedMammogram.LocationType.OUTSIDE_UK.value
        PREFER_NOT_TO_SAY = (
            ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY.value
        )

    def __init__(self, participant, current_provider, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.participant = participant
        self.current_provider = current_provider
        self.where_taken_choices = {
            self.WhereTaken.SAME_UNIT: f"At {current_provider.name}",
            self.WhereTaken.ANOTHER_UNIT: "At another NHS breast screening unit",
            self.WhereTaken.ELSEWHERE_UK: "Somewhere else in the UK",
            self.WhereTaken.OUTSIDE_UK: "Outside the UK",
            self.WhereTaken.PREFER_NOT_TO_SAY: "Prefer not to say",
        }

        self.when_taken_choices = {
            "exact": "Enter an exact date",
            "approx": "Enter an approximate date",
            "not_sure": "Not sure",
        }

        self.name_is_the_same_legend = {
            "text": f"Were they taken with the name {participant.full_name}?",
            "classes": "nhsuk-fieldset__legend--m",
            "isPageHeading": False,
        }

        self.name_is_the_same_choices = {
            "yes": "Yes",
            "no": "No, under a different name",
        }

        # Add additional fields which are used on the form for progressively disclosing
        # other form fields
        self.fields["where_taken"] = ChoiceField(choices=self.where_taken_choices)

        self.fields["when_taken"] = ChoiceField(choices=self.when_taken_choices)

        self.fields["name_is_the_same"] = ChoiceField(
            choices=self.name_is_the_same_choices
        )

        # Explicitly order the films so that the error summary order
        # matches the order fields are rendered in.
        self.order_fields(
            [
                "where_taken",
                "provider",
                "location_details",
                "when_taken",
                "exact_date",
                "approx_date",
                "name_is_the_same",
                "different_name",
                "additional_information",
            ]
        )

    def clean(self):
        cleaned_data = super().clean()

        where_taken = cleaned_data.get("where_taken")
        when_taken = cleaned_data.get("when_taken")
        name_is_the_same = cleaned_data.get("name_is_the_same")

        if where_taken == self.WhereTaken.SAME_UNIT:
            self.cleaned_data["provider"] = self.current_provider
        elif where_taken == self.WhereTaken.ANOTHER_UNIT and not cleaned_data.get(
            "provider"
        ):
            self.add_error(
                "provider",
                ValidationError(
                    "Select another brest screening unit.", code="required"
                ),
            )
        elif where_taken in (
            self.WhereTaken.ELSEWHERE_UK,
            self.WhereTaken.OUTSIDE_UK,
        ) and not cleaned_data.get("location_details"):
            self.add_error(
                "location_details",
                ValidationError(
                    "Provide the clinic or hospital name, or any location details.",
                    code="required",
                ),
            )

        if when_taken == "exact" and not cleaned_data.get("exact_date"):
            self.add_error(
                "exact_date",
                ValidationError("Provide the date.", code="required"),
            )
        elif when_taken == "approx" and not cleaned_data.get("approx_date"):
            self.add_error(
                "approx_date",
                ValidationError("Provide the approximate date.", code="required"),
            )

        if name_is_the_same == "no" and not cleaned_data.get("different_name"):
            self.add_error(
                "different_name",
                ValidationError("Provide the previous name.", code="required"),
            )

    def set_location_type(self, instance):
        where_taken = self.cleaned_data["where_taken"]
        if where_taken in (self.WhereTaken.SAME_UNIT, self.WhereTaken.ANOTHER_UNIT):
            instance.location_type = (
                ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT
            )
        else:
            instance.location_type = where_taken

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.participant = self.participant
        self.set_location_type(instance)

        if commit:
            instance.save()

        return instance
