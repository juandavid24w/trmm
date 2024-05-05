from barcodes.widgets import BarcodeTextInput


class ISBNSearchInput(BarcodeTextInput):
    template_name = "books/text.html"
    isbn_search_submit_name = "_isbnsearch"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["isbn_search_submit_name"] = self.isbn_search_submit_name

        return context
