class DefaultObjectAdminMixin:
    def get_list_display(self, request):
        ld = super().get_list_display(request)
        return [*ld, "is_default"]
