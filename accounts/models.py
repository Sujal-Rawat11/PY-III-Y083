from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from base.emails import send_account_activation_email

class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile', null=True, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_profile_and_send_email(sender, instance, created, **kwargs):
    if created:
        import uuid
        from base.emails import send_account_activation_email

        email_token = str(uuid.uuid4())
        Profile.objects.create(user=instance, email_token=email_token)

        try:
            send_account_activation_email(instance.email, email_token)
        except Exception as e:
            # Log the error, but don't crash registration
            print("Email sending failed:", e)
