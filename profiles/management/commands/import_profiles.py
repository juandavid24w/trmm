import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import Profile

User = get_user_model()

xlsx_file = settings.BASE_DIR / "data" / "matriz.xlsx"


class Command(BaseCommand):
    help = "Import profiles from XLSX"

    def handle(self, *args, **options):
        for grade in ("6EF", "7EF", "8EF", "9EF", "1EM", "2EM", "3EM"):
            self.stdout.write(f"Adicionando {grade}...")

            df = pd.read_excel(xlsx_file, sheet_name=grade)
            df = df[df["RM"].notnull()]
            df["RM"] = df["RM"].astype(int)

            for _, row in df.iterrows():
                names = row[df.columns[3]].split()
                email = row[df.columns[26]]

                if User.objects.filter(email=email):
                    self.stdout.write(
                        f"Usuário {' '.join(names)} já existente. "
                        "Atualizando RM..."
                    )
                    user = User.objects.get(email=email)
                    user.profile.id_number = row["RM"]
                    user.profile.save()
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
                )

                user.set_password(password)
                profile = Profile(user=user)
                user.save()
                profile.save()

                for email in additional_emails:
                    user.additional_emails.create(email=email)
