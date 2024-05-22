from django.shortcuts import get_object_or_404, redirect


class HiddenAdminMixin:
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

    def base_redirect_view(self, action, request, object_id):
        field = self.redirect_related_fields[action]

        if object_id:
            obj = get_object_or_404(self.model, pk=object_id)
            related = getattr(obj, field)
            args = (related.pk,)
        else:
            related = self.model._meta.get_field(field).related_model
            args = ()

        code = (
            f"admin:{related._meta.app_label}_"
            f"{related._meta.model_name}_{action}"
        )
        response = redirect(code, *args)
        if popup := request.GET.get("_popup"):
            response["Location"] += f"?_popup={popup}"
        return response

    def change_view(
        self, request, object_id, form_url="", extra_context=None
    ):
        try:
            return self.base_redirect_view("change", request, object_id)
        except (AttributeError, KeyError):
            return super().change_view(
                request, object_id, form_url, extra_context
            )

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return self.base_redirect_view("delete", request, object_id)
        except (AttributeError, KeyError):
            return super().delete_view(request, object_id, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        try:
            return self.base_redirect_view("add", request, object_id=None)
        except (AttributeError, KeyError):
            return super().delete_view(self, request, form_url, extra_context)
