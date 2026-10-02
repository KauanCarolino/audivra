from django.db import models


class Note(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(default=1)
    active = models.BooleanField(default=True)
    password = models.CharField(max_length=128, blank=True, default="")
    token = models.CharField(max_length=128, blank=True, default="")
    secret = models.CharField(max_length=128, blank=True, default="")
    cpf = models.CharField(max_length=14, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    author = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        app_label = "tracking"
