from django import forms

WEEK_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def days_to_bitmask(selected_days):
    """将 ['Mon','Sun'] 转为整数 bitmask"""
    bit = 0
    for i, name in enumerate(WEEK_LABELS):
        if name in selected_days:
            bit |= (1 << i)
    return bit

class PreferenceForm(forms.Form):
    week_no = forms.IntegerField(min_value=1, max_value=10)
    daily_hours = forms.FloatField(min_value=0, max_value=24, required=False)
    weekly_study_days = forms.IntegerField(min_value=0, max_value=7, required=False)
    mode = forms.ChoiceField(choices=[("manual", "manual"), ("default", "default")])
    avoid_days = forms.MultipleChoiceField(
        required=False,
        choices=[(x, x) for x in WEEK_LABELS],
        widget=forms.CheckboxSelectMultiple
    )
