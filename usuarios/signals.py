from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import User, UserProfile
from .permissions import assign_user_role_group, sync_role_groups


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_migrate)
def sync_permission_groups_after_migrate(sender, **kwargs):
    if getattr(sender, "name", None) != "usuarios":
        return
    sync_role_groups(force=True)


@receiver(user_logged_in)
def sync_user_groups_on_login(sender, user, request, **kwargs):
    assign_user_role_group(user)
