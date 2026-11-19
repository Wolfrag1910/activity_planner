from django.utils import translation


class MemberLanguageMiddleware:
    """
    Show a signed-in member the site in the language saved on their account,
    so it's the same on their phone and their laptop. Visitors who aren't
    signed in get the language from the RO/EN button (a cookie) or Romanian.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        member = getattr(request, "user", None)
        if member is not None and member.is_authenticated and member.language:
            translation.activate(member.language)
            request.LANGUAGE_CODE = member.language
        return self.get_response(request)
