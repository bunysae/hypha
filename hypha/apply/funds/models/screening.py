from django.db import models
from django.utils.translation import gettext_lazy as _


class ScreeningStatus(models.Model):
    title = models.CharField(max_length=128)
    is_archived = models.BooleanField(default=False, verbose_name=_("Archived"))

    class Meta:
        verbose_name_plural = "screening statuses"

    def __str__(self):
        return self.title if not self.is_archived else f'{self.title} (archived)'
