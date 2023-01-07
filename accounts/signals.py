from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import UserProfile, User

@receiver(post_save, sender=User)
def post_save_create_profile_receiver(sender, instance, created, **kwargs ):
    # this signal gets activates just after user is created
    if created:
        UserProfile.objects.create(user=instance)
        print("user profile created")
    else:
        try:
            profile = UserProfile.objects.get(user=instance)
            profile.save()
            print("user updated")
        except:
            UserProfile.objects.create(user=instance)
            print("user profile created")


@receiver(pre_save, sender=User)         
def  post_save_profile_receiver(sender, instance, **kwargs):
    print("this user is being saved -> ", instance.username )