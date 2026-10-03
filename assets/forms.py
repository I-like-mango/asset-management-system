from django import forms

from assets.models import Asset, AssetCategory, AssetLoan


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "asset_no",
            "name",
            "category",
            "brand",
            "model",
            "serial_no",
            "status",
            "location",
            "purchase_date",
            "warranty_until",
            "price",
            "remark",
        ]
        widgets = {
            "asset_no": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "serial_no": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "purchase_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "warranty_until": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "remark": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = AssetCategory.objects.filter(is_active=True)


class AssetFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        label="设备类型",
        queryset=AssetCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status = forms.ChoiceField(
        label="设备状态",
        choices=[("", "全部")] + list(Asset._meta.get_field("status").choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(label="关键字", required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    loaned_from = forms.DateField(
        label="领用开始",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    loaned_to = forms.DateField(
        label="领用结束",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    due_from = forms.DateField(
        label="到期开始",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    due_to = forms.DateField(
        label="到期结束",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    overdue = forms.BooleanField(label="仅逾期", required=False)


class LoanApplyForm(forms.ModelForm):
    class Meta:
        model = AssetLoan
        fields = ["asset", "purpose", "expected_return_at"]
        widgets = {
            "asset": forms.Select(attrs={"class": "form-select"}),
            "purpose": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "expected_return_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from common.constants import AssetStatus

        self.fields["asset"].queryset = Asset.objects.filter(is_deleted=False, status=AssetStatus.IN_STOCK)


class ApprovalForm(forms.Form):
    comment = forms.CharField(
        label="审批意见",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )


class ImportForm(forms.Form):
    file = forms.FileField(label="Excel 文件", widget=forms.FileInput(attrs={"class": "form-control"}))


class ExportForm(forms.Form):
    fields = forms.MultipleChoiceField(
        label="导出字段",
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        from assets.services.import_export_service import EXPORT_FIELD_MAP

        super().__init__(*args, **kwargs)
        self.fields["fields"].choices = [(k, v) for k, v in EXPORT_FIELD_MAP.items()]
