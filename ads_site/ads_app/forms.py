from django import forms


class CreateDash(forms.Form):
    folder_name = forms.CharField(max_length=250)
    url = forms.CharField(max_length=250, required=False)
    global_path = forms.CharField(max_length=250)
    target_choice = forms.CharField(max_length=250)
    short_name = forms.CharField(max_length=250)
    test_choice = forms.CharField(max_length=250)
    test_plan_name = forms.CharField(max_length=250)
