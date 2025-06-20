from django import forms
from .models import Ethnicity


class EthnicityForm(forms.Form):
    ethnic_group_choice = forms.ChoiceField(
        choices=Ethnicity.ethnic_groups_with_display_names(),
        required=True,
        error_messages={"required": "An ethnic group must be selected"},
    )

    def __init__(self, *args, **kwargs):
        if "participant" not in kwargs:
            raise ValueError("EthnicGroupForm requires a participant")
        self.participant = kwargs.pop("participant")
        super().__init__(*args, **kwargs)

        # TODO: can this be moved outside of init?
        for ethnic_group in self.non_specific_ethnic_groups():
            self.fields[ethnic_group + "_details"] = forms.CharField(required=False)

    def ethnic_groups_by_category(self):
        return Ethnicity.DATA.items()

    def non_specific_ethnic_groups(self):
        return Ethnicity.non_specific_ethnic_groups()
