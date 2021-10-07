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


# mixin DfesAdminModelMixin
class ExternalUserAdmin(DfesAdminModelMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "username",
    )

    # and implement get_list method to return
    # `{"total": <total number or items>, "items": <list of ExternalUser instances>}`
    def get_list(self, request, page_num, list_per_page):

        # pull data from some service
        data = {
            "total": 1,
            "users": [
                {"id": 1, "username": "User1"},
            ],
        }

        items = [ExternalUser(**i) for i in data.get("users") or []]

        return {
            "total": data.get("total") or 0,
            "items": items,
        }

    # other django admin customization


admin.site.register(ExternalUser, ExternalUserAdmin)
