from django.db import models


class ReportingMonth(models.Model):
    """
    Example code:
    202512 = December 2025
    202601 = January 2026
    """

    code = models.CharField(
        max_length=6, unique=True, help_text="Format: YYYYMM (e.g. 202512)"
    )

    year = models.IntegerField(editable=False)
    month = models.IntegerField(editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        code -> year & month auto extract
        """
        if len(self.code) != 6:
            raise ValueError("Month code must be YYYYMM format")

        self.year = int(self.code[:4])
        self.month = int(self.code[4:6])

        if self.month < 1 or self.month > 12:
            raise ValueError("Invalid month in code")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.code
