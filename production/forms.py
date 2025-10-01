from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Excel faylni tanlang",
        help_text="Faqat .xlsx fayl yuklang"
    )
