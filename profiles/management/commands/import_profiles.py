import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import Profile

User = get_user_model()

xlsx_file = settings.BASE_DIR / "matriz.xlsx"


class Command(BaseCommand):
    help = "Import profiles from XLSX"

    def handle(self, *args, **options):
        for grade in Profile.Grade:
            self.stdout.write(f"Adicionando {grade}...")

            df = pd.read_excel(xlsx_file, sheet_name=grade)
            df = df[df["RM"].notnull()]
            df["RM"] = df["RM"].astype(int)

            for _, row in df.iterrows():
                names = row[df.columns[3]].split()

                email = row[df.columns[26]]
                if User.objects.filter(email=email):
                    self.stdout.write(
                        f"Usuário {' '.join(names)} já existente. Ignorando..."
                    )
                    continue


                poss_usernames = (
                    ".".join(map(slugify, [names[0], *names[-i:]]))
                    for i in range(1, len(names))
                )

                username = next(
                    u
                    for u in poss_usernames
                    if not User.objects.filter(username=u)
                )

                additional_emails = row[df.columns[7]].split(",")

                if pd.isnull(row["Data de nascimento"]):
                    password = names[0][0].strip().lower() + "01012000"
                else:
                    password = names[0][0].strip().lower() + row[
                        "Data de nascimento"
                    ].strftime("%d%m%Y")

                user = User(
                    username=username,
                    first_name=names[0],
                    last_name=" ".join(names[1:]),
                    email=email,
                    password=password,
                )

                profile = Profile(user=user, grade=grade)
                user.save()
                profile.save()

                group, _ = Group.objects.get_or_create(name="Estudantes")
                user.groups.add(group)

                for email in additional_emails:
                    user.additional_emails.create(email=email)
