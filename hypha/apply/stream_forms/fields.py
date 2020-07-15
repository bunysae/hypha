from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import FileExtensionValidator
from django.forms import CheckboxInput, ClearableFileInput, FileField, Media
from django.utils.functional import cached_property
from django_file_form.forms import MultipleUploadedFileField
from django_file_form.widgets import UploadMultipleWidget


class MultiFileInput(ClearableFileInput):
    """
    File Input only returns one file from its clean method.

    This passes all files through the clean method and means we have a list of
    files available for post processing
    """
    template_name = 'stream_forms/fields/multi_file_field.html'

    input_text = ''

    def __init__(self, *args, **kwargs):
        self.multiple = kwargs.pop('multiple', True)
        super().__init__(*args, **kwargs)

    def is_initial(self, value):
        is_initial = super().is_initial
        if not value:
            return False

        try:
            return all(
                is_initial(file) for file in value
            )
        except TypeError:
            return is_initial(value)

    def render(self, name, value, attrs=dict(), renderer=None):
        if self.multiple:
            attrs['multiple'] = 'multiple'

        return super().render(name, value, attrs, renderer)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            upload = files.getlist(name)
        else:
            upload = files.get(name)
            if not isinstance(upload, list):
                upload = [upload]

        checkbox_name = self.clear_checkbox_name(name) + '-'
        checkboxes = {k for k in data if checkbox_name in k}
        cleared = {
            int(checkbox.replace(checkbox_name, '')) for checkbox in checkboxes
            if CheckboxInput().value_from_datadict(data, files, checkbox)
        }

        return {
            'files': upload,
            'cleared': cleared,
        }


class CustomUploadMultipleWidget(UploadMultipleWidget):

    # This file seems to be imported even during collectstatic,
    # at which point `static()` won't be able to find these files yet
    # using production settings, so we delay calling `static()` until it's needed.
    @cached_property
    def media(self):
        return Media(
            css={'all': [
                static('file_form/file_form.css'),
            ]},
            js=[
                static('file_form/file_form.js'),
                static('js/apply/file-uploads.js'),
            ],
        )


class MultiFileField(MultipleUploadedFileField):
    widget = CustomUploadMultipleWidget

    def clean(self, value, initial):
        # TODO: Re-enable validation here, and check if we still need any overrides
        # from MultiFileInput to be present in CustomUploadMultipleWidget too.
        return super().clean(value, initial)

        files = value['files']
        cleared = value['cleared']
        if not files and not cleared:
            return initial
        new = [
            FileField(validators=[
                FileExtensionValidator(allowed_extensions=settings.FILE_ALLOWED_EXTENSIONS)
            ]).clean(file, initial) for file in files
        ]

        if initial:
            old = [file for i, file in enumerate(initial) if i not in cleared]
        else:
            old = []

        return old + new

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, MultiFileInput) and 'accept' not in widget.attrs:
            attrs.setdefault('accept', settings.FILE_ACCEPT_ATTR_VALUE)
        return attrs
