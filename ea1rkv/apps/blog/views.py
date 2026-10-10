from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext as _, override
from django.views.decorators.csrf import csrf_protect

from .forms import CommentForm
from .models import BlogComment


@csrf_protect
def serve_blog(request, page):
    if request.method not in ("GET", "HEAD", "POST"):
        return HttpResponseNotAllowed(["GET", "HEAD", "POST"])
    with override(page.locale.language_code):
        context = page.get_context(request)
        status = 200
        if request.method == "POST":
            form = CommentForm(request.POST)
            context["comment_form"] = form
            # Wagtail routes the request through its page privacy checks first.
            published = page.live_revision.as_object() if page.live_revision_id else page
            if not page.live or not published.comments_enabled:
                form.add_error(None, _("Los comentarios están cerrados."))
                status = 403
            elif form.is_valid():
                if form.cleaned_data["website"]:
                    return redirect(page.get_url(request) + "#comments")
                # No raw IP is stored. A short-lived hash limits repeated submissions.
                key = "blog-comment:" + salted_hmac("blog-comment", request.META.get("REMOTE_ADDR", "")).hexdigest()
                if not cache.add(key, True, timeout=60):
                    form.add_error(None, _("Espera un minuto antes de enviar otro comentario."))
                    status = 429
                else:
                    BlogComment.objects.create(page=page, name=form.cleaned_data["name"], text=form.cleaned_data["text"])
                    messages.success(request, _("Comentario recibido. Aparecerá cuando lo apruebe un administrador."))
                    return redirect(page.get_url(request) + "#comments")
            else:
                status = 400
        response = TemplateResponse(request, page.get_template(request), context, status=status)
        response.render()
        return response
