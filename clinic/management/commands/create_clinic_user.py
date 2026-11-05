from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create an application user and assign the Staff or Doctor role."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--role", choices=["Staff", "Doctor"], required=True)
        parser.add_argument("--email", default="")

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username=options["username"]).exists():
            raise CommandError("That username already exists.")
        password = None
        while not password:
            first, second = self.get_password()
            if first != second:
                self.stderr.write("Passwords do not match. Try again.")
                continue
            try:
                validate_password(first, User(username=options["username"], email=options["email"]))
            except ValidationError as exc:
                self.stderr.write(str(exc))
                continue
            password = first
        user = User.objects.create_user(username=options["username"], email=options["email"], password=password)
        user.groups.add(Group.objects.get(name=options["role"]))
        self.stdout.write(self.style.SUCCESS(f"Created {options['role']} account {user.username}."))

    def get_password(self):
        from getpass import getpass
        first = getpass("Password: ")
        second = getpass("Confirm password: ")
        return first, second
