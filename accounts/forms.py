from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import Group, User

from accounts.models import Department, UserProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="用户名", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="密码", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label="密码",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="留空则不修改密码",
    )
    groups = forms.ModelChoiceField(
        label="角色",
        queryset=Group.objects.filter(name__in=["ADMIN", "USER"]),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    department = forms.ModelChoiceField(
        label="部门",
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    employee_no = forms.CharField(label="工号", required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(label="手机", required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class RolePermissionForm(forms.Form):
    permissions = forms.MultipleChoiceField(
        label="权限",
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        from common.constants import PERMISSION_CODES

        super().__init__(*args, **kwargs)
        self.fields["permissions"].choices = [(k, v) for k, v in PERMISSION_CODES.items()]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "employee_no", "department"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "employee_no": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-select"}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
