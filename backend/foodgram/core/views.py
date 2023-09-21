# from django.shortcuts import render


# def handler404(request, exception=None, template_name="404.html"):
#     return render(request, template_name, status=404)

from django.views.defaults import page_not_found


def handler_404(request, exception):
    return page_not_found(request, exception, template_name="404.html")
