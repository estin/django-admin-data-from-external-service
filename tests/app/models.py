from django.db import models
from django.contrib import admin

from dadfes.admin import DfesAdminModelMixin


# Declare model for external data (managed: false)
class ExternalUser(models.Model):
    id = models.IntegerField("Id", primary_key=True)
    username = models.TextField("Username")

    class Meta:
        managed = False
        verbose_name = "External User Model"


# 1. mixin DfesAdminModelMixin
class ExternalUserAdmin(DfesAdminModelMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "username",
    )

    # 2. and implement get_list method with returning
    # `{"total": <total number or items>, "items": <list of ExternalUser instances>}`
    def get_list(self, request, page_num, list_per_page):

        # 2.1 pull data from some service, where
        #   search = request.GET.get('q')
        #   order_by = request.GET.get('o')
        #   some_list_filter = request.GET.get('some_list_filter')
        data = {
            "total": 1,
            "users": [
                {"id": 1, "username": "User1"},
            ],
        }

        # 2.2 map data to model instances
        items = [ExternalUser(**i) for i in data.get("users") or []]

        return {
            "total": data.get("total") or 0,
            "items": items,
        }

    # 3. other standart django admin customization
    def get_object(self, request, object_id, *args, **kwargs):
        # 3.1 fetch object from external service
        user = {"id": 1, "username": "User1"}
        # 3.2 map data to model instance
        return ExternalUser(**user)


admin.site.register(ExternalUser, ExternalUserAdmin)
