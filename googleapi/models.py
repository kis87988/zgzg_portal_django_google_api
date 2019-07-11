from django.db import models

# Create your models here.


class UserAccessRecord(models.Model):
    email = models.EmailField()
    access_token = models.TextField()
    first_issued_at = models.TimeField()
    id_token = models.TextField()
    login_hint = models.TextField()
    expires_at = models.TimeField()
    expires_in = models.TimeField()
    ip_address = models.TextField()
    record_time = models.DateTimeField()
    action = models.TextField()
    def __str__(self):
        return f"{self.email}:{self.record_time}:{self.action}"

