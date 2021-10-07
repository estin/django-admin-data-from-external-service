import requests

from functools import cache

from django.db import models
from django.contrib import admin

from dadfes.admin import DfesAdminModelMixin


GITHUB_API_ORG_URL = "https://api.github.com/orgs/django"
GITHUB_API_REPOS_URL = "https://api.github.com/orgs/django/repos"
GITHUB_API_REPO_URL = "https://api.github.com/repos/{}"


class Repository(models.Model):
    id = models.IntegerField("Id")
    name = models.TextField("Name")
    full_name = models.TextField("Full Name", primary_key=True)
    forks_count = models.IntegerField("Forks")
    stargazers_count = models.IntegerField("Stars")
    watchers_count = models.IntegerField("Watchers")
    open_issues_count = models.IntegerField("Open Issues")

    @classmethod
    @cache
    def _fields_names(cls):
        return [f.name for f in Repository._meta.fields]

    @classmethod
    def build_from(cls, data):
        return Repository(**dict((field, data.get(field)) for field in cls._fields_names()))

    class Meta:
        managed = False
        verbose_name = "Repository"
        verbose_name_plural = "Repositories"


# https://docs.github.com/en/rest/reference/repos
class RepositoryAdmin(DfesAdminModelMixin, admin.ModelAdmin):
    list_per_page = 10
    list_display = (
        "id",
        "full_name",
        "stargazers_count",
        "forks_count",
        "watchers_count",
        "open_issues_count",
    )
    sortable_by = []

    @cache
    def _get_repos_total(self):
        response = requests.get(
            GITHUB_API_ORG_URL,
        )

        data = response.json()
        return data.get("public_repos")

    def get_readonly_fields(self, request, obj=None):
        return Repository._fields_names()

    def get_list(self, request, page_num, list_per_page):

        response = requests.get(
            GITHUB_API_REPOS_URL,
            params={
                "page": page_num or 1,
                "per_page": list_per_page or self.list_per_page,
            },
        )

        # rate limit error
        if response.status_code == 403:
            return {
                "items": [],
            }

        data = response.json()

        items = [Repository.build_from(item) for item in data or []]

        return {
            "total": self._get_repos_total(),
            "items": items,
        }

    def get_object(self, request, object_id, *args, **kwargs):
        response = requests.get(
            GITHUB_API_REPO_URL.format(object_id),
        )
        return Repository.build_from(response.json())

    def has_module_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated

    def has_change_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated

    def has_add_permission(self, request, *args, **kwargs):
        return False

    def has_delete_permission(self, request, *args, **kwargs):
        return False

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                "show_save_and_continue": False,
                "show_save": False,
            }
        )
        return super().change_view(request, object_id, extra_context=extra_context)


admin.site.register(Repository, RepositoryAdmin)
