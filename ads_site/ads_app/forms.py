from django import forms


class CreateDash(forms.Form):
    folder_name = forms.CharField(max_length=250)
    url = forms.CharField(max_length=250, required=False)
    global_path = forms.CharField(max_length=250)
    target_choice1 = forms.CharField(max_length=250)
    target_choice2 = forms.CharField(max_length=250, required=False)
    target_choice3 = forms.CharField(max_length=250, required=False)
    target_name1 = forms.CharField(max_length=250)
    target_name2 = forms.CharField(max_length=250, required=False)
    target_name3 = forms.CharField(max_length=250, required=False)
    test_choice = forms.CharField(max_length=250)
    test_plan_name = forms.CharField(max_length=250)
