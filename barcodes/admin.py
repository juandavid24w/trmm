from django import forms


# pylint: disable-next: too-few-public-methods
class BarcodeSearchBoxMixin:
    change_list_template = "barcodes/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["original_template"] = (
            super().change_list_template or "admin/change_list.html"
        )

        return super().changelist_view(request, extra_context)

    @property
    def media(self):
        return super().media + forms.Media(
            css={"all": ["barcodes/style.css"]},
            js=[
                "barcodes/script.js",
                "https://cdn.jsdelivr.net/npm/@undecaf/zbar-wasm@0.9.15/dist/index.js",
                "https://cdn.jsdelivr.net/npm/@undecaf/barcode-detector-polyfill@0.9.20/"
                + "dist/index.js",
            ],
        )
