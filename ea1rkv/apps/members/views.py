from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache


def password_token():
    password = getattr(settings, "CLUB_DOCUMENTS_PASSWORD", "")
    return salted_hmac("club-documents", password).hexdigest() if password else ""


def allowed(request):
    token = password_token()
    return bool(token and constant_time_compare(request.session.get("club_documents", ""), token))


@never_cache
@csrf_protect
def documents_page(request, page):
    error = ""
    if request.method == "POST":
        if "logout" in request.POST:
            request.session.pop("club_documents", None)
            return redirect(page.url)
        key = "club-login:" + salted_hmac("club-ip", request.META.get("REMOTE_ADDR", "")).hexdigest()
        attempts = cache.get(key, 0)
        if attempts >= 10:
            error = "Demasiados intentos. Vuelve a intentarlo dentro de 15 minutos."
        elif password_token() and constant_time_compare(request.POST.get("password", ""), settings.CLUB_DOCUMENTS_PASSWORD):
            request.session.cycle_key()
            request.session["club_documents"] = password_token()
            return redirect(page.url)
        else:
            cache.set(key, attempts + 1, 900)
            error = "Contraseña incorrecta o acceso todavía sin configurar."
    authorized = allowed(request)
    # Use the published revision so saved drafts cannot leak into downloads.
    published = page.live_revision.as_object() if page.live_revision_id else page
    response = render(request, "members/documents.html", {
        "page": page, "authorized": authorized, "error": error,
        "private_intro": published.intro if authorized else "",
        "documents": published.private_documents.all() if authorized else [],
    })
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@never_cache
def download(request, page_id, document_id):
    from .models import ClubDocumentsPage
    page = ClubDocumentsPage.objects.live().filter(pk=page_id).first()
    if page is None or not page.live_revision_id:
        raise Http404
    if not allowed(request):
        return redirect(page.url)
    published = page.live_revision.as_object()
    document = next((d for d in published.private_documents.all() if d.download_key == document_id), None)
    if document is None:
        raise Http404
    response = FileResponse(document.file.open("rb"), as_attachment=True, filename=document.file.name.rsplit("/", 1)[-1])
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["X-Content-Type-Options"] = "nosniff"
    return response
