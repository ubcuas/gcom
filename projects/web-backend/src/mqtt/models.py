from django.db import models


class Data(models.Model):
    """
    Represents the structure of the MQTT data message.
    """

    id = models.CharField(max_length=16, primary_key=True)
    MSG_TYPE_CHOICES = [
        ("TYPE1", "Type 1"),
        ("TYPE2", "Type 2"),
        ("TYPE3", "Type 3"),
    ]
    msg_type = models.CharField(max_length=20, choices=MSG_TYPE_CHOICES)
    message = models.JSONField()
    timestamp = models.FloatField()

    def __str__(self):
        return f"{self.id} - {self.msg_type} @ {self.timestamp}"
