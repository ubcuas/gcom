from django.db import models


class Data(models.Model):
    """
    Represents the structure of the MQTT data message.
    """

    id = models.CharField(max_length=16, primary_key=True)
    MSG_TYPE_CHOICES = [
        ("TAKE_PHOTO", "Take Photo"),
        ("TYPE2", "Type 2"),
        ("TYPE3", "Type 3"),
    ]
    action = models.CharField(max_length=20, choices=MSG_TYPE_CHOICES)
    message = models.JSONField(null=True, blank=True)
    timestamp = models.FloatField()

    def __str__(self):
        return f"{self.id} - {self.msg_type} @ {self.timestamp}"
