from django.db import models
from ..admin_forms import ScreeningStatusAdminForm


class ScreeningStatus(models.Model):
    title = models.CharField(max_length=128)
    yes = models.BooleanField(default=False, verbose_name="Yes/No")
    default = models.BooleanField(default=False, verbose_name="Default Yes/No")

    base_form_class = ScreeningStatusAdminForm

    class Meta:
        verbose_name_plural = "screening statuses"

    def __str__(self):
        return self.title
