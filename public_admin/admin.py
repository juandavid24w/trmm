class PublicAdminSiteMixin:
    index_template = "public_admin/index.html"

    def has_permission(self, request):
        return True

    def each_context(self, request, *args, **kwargs):
        context = super().each_context(request, *args, **kwargs) or {}
        context["is_public_admin"] = True

        return context


class PublicModelAdminMixin:
    def get_model_perms(self, request, *args, **kwargs):
        return {"view": True}

    def has_module_permission(self, request, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_view_permission(self, *args, **kwargs):
        return True
