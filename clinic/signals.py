from django.contrib.auth.models import Group


def create_roles(sender, **kwargs):
    Group.objects.get_or_create(name="Staff")
    Group.objects.get_or_create(name="Doctor")
