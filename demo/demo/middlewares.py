from django.contrib.auth import get_user_model, login


class AutoLoginMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if not request.user.is_authenticated and "/login" not in request.path:

            User = get_user_model()

            viewer, created = User.objects.get_or_create(
                username="viewer",
                is_staff=True,
                is_superuser=False,
            )

            login(request, viewer)

        return self.get_response(request)
