from django.contrib.auth.models import Group, Permission, User

from loans.models import Period, Renewal
from site_configuration.models import SiteConfiguration

Period(description="Acervo fixo", days=15).save()
Period(description="Acervo móvel", days=30).save()
Renewal(description="Primeira renovação", days=15, order=1).save()
Renewal(description="Segunda renovação", days=15, order=2).save()

usergroup, _ = Group.objects.get_or_create(name="Usuário")
usergroup.permissions.add(Permission.objects.get(codename="view_book"))
usergroup.permissions.add(Permission.objects.get(codename="view_specimen"))
usergroup.permissions.add(
    Permission.objects.get(codename="view_classification")
)
usergroup.permissions.add(Permission.objects.get(codename="view_location"))
usergroup.permissions.add(Permission.objects.get(codename="view_loan"))
usergroup.permissions.add(Permission.objects.get(codename="view_period"))
usergroup.permissions.add(Permission.objects.get(codename="view_renewal"))

for user in User.objects.all():
    user.groups.add(usergroup)

modgroup, _ = Group.objects.get_or_create(name="Moderador")
modgroup.permissions.add(Permission.objects.get(codename="view_book"))
modgroup.permissions.add(Permission.objects.get(codename="add_book"))
modgroup.permissions.add(Permission.objects.get(codename="change_book"))
modgroup.permissions.add(Permission.objects.get(codename="delete_book"))
modgroup.permissions.add(Permission.objects.get(codename="view_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="add_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="change_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="delete_specimen"))
modgroup.permissions.add(
    Permission.objects.get(codename="view_classification")
)
modgroup.permissions.add(Permission.objects.get(codename="view_location"))
modgroup.permissions.add(Permission.objects.get(codename="view_loan"))
modgroup.permissions.add(Permission.objects.get(codename="add_loan"))
modgroup.permissions.add(Permission.objects.get(codename="change_loan"))
modgroup.permissions.add(Permission.objects.get(codename="delete_loan"))
modgroup.permissions.add(Permission.objects.get(codename="view_period"))
modgroup.permissions.add(Permission.objects.get(codename="view_renewal"))
modgroup.permissions.add(
    Permission.objects.get(codename="view_documentationpage")
)
modgroup.permissions.add(
    Permission.objects.get(codename="change_documentationpage")
)
modgroup.permissions.add(
    Permission.objects.get(codename="add_documentationpage")
)
modgroup.permissions.add(
    Permission.objects.get(codename="delete_documentationpage")
)
