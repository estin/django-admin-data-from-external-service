import json
import requests

from functools import cache

from django.db import models
from django.contrib import admin
from django import forms
from dadfes.admin import DfesAdminModelMixin


CLICKHOUSE_API_TIMEOUT = 10
CLICKHOUSE_API_URL = "https://gh-api.clickhouse.com/?add_http_cors_header=1&user=play&password=&default_format=JSONCompact&max_result_rows=1000&max_result_bytes=10000000&result_overflow_mode=break"  # noqa

CLICKHOUSE_LIST_SQL_TEMPLATE = """
SELECT
    link
    ,title
    ,length(NER) ner_length
    ,length(directions) directions_length
    ,NER ner
    ,ingredients
    ,directions
    --,source
FROM recipes
{where}
ORDER BY {order_by}
LIMIT {limit}
OFFSET {offset}
FORMAT JSON
"""

CLICKHOUSE_TOP_INGRIDIENTS_SQL = """
SELECT
    arrayJoin(NER) AS ingredient,
    count() AS c
FROM recipes
GROUP BY ingredient
ORDER BY c DESC
LIMIT 10
FORMAT JSON
"""


def prevent_injection(s):
    return s.replace("'", "").replace(";", "")


class PrettyJsonListWidget(forms.widgets.Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        items = json.loads(value or "[]")

        try:
            return "<ul>{}</ul>".format("".join(["<li>{}</li>".format(i) for i in items]))
        except Exception as e:
            return str(e)

    def value_from_datadict(self, data, files, name):
        return data.get(name) or "[]"


class Recipe(models.Model):
    link = models.TextField("link", max_length=1024 * 3, primary_key=True)
    title = models.CharField("Title", max_length=1024 * 3)
    ner_length = models.TextField("NER length")
    directions_length = models.TextField("Directions length")
    ner = models.JSONField("NER")
    ingredients = models.JSONField("Ingredients")
    directions = models.JSONField("Directions")
    # source = models.TextField("Source")

    @classmethod
    @cache
    def _fields_names(cls):
        return [f.name for f in Recipe._meta.fields]

    @classmethod
    def build_from(cls, data):
        return Recipe(**dict((field, data.get(field)) for field in cls._fields_names()))

    class Meta:
        managed = False
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"


class HasIngredientFilter(admin.SimpleListFilter):
    title = "Has ingredient"
    parameter_name = "has_ingredient"

    @cache
    def lookups(self, request, model_admin):
        response = requests.post(
            CLICKHOUSE_API_URL,
            data=CLICKHOUSE_TOP_INGRIDIENTS_SQL,
            timeout=CLICKHOUSE_API_TIMEOUT,
        )
        response.raise_for_status()

        result = response.json()

        return [[i.get("ingredient")] * 2 for i in result.get("data")]


# https://docs.github.com/en/rest/reference/repos
class RecipeAdmin(DfesAdminModelMixin, admin.ModelAdmin):
    list_per_page = 100
    search_fields = ("title",)
    list_display = (
        "title",
        "ner_length",
        "directions_length",
        "link",
    )
    sortable_by = [
        "title",
        "ner_length",
        "directions_length",
    ]
    fields = [
        "title",
        "link",
        "ingredients",
        "directions",
    ]
    list_filter = (HasIngredientFilter,)

    formfield_overrides = {
        models.JSONField: {"widget": PrettyJsonListWidget},
    }

    def get_readonly_fields(self, request, obj=None):
        return self.list_display

    def _get_where_clause(self, request):
        search = request.GET.get("q")
        has_ingredient = request.GET.get("has_ingredient")
        if not search and not has_ingredient:
            return ""
        cond = []
        if search:
            # TODO avoid of sql injection!!!
            cond.append("title ilike '%{}%'".format(prevent_injection(search)))
        if has_ingredient:
            # TODO avoid of sql injection!!!
            cond.append("has(NER, '{}')".format(prevent_injection(has_ingredient)))
        return "WHERE {}".format(" and ".join(cond))

    def _get_order_by_clause(self, request):
        order_by = request.GET.get("o")
        sort = []
        if not order_by:
            sort.append("ner_length desc")
        else:
            for item in order_by.split("."):
                direction = "desc" if item.startswith("-") else "asc"
                item = item.replace("-", "")
                if not item.isdigit():
                    continue
                try:
                    field = self.sortable_by[int(item)]
                except IndexError:
                    continue
                if not field:
                    continue
                sort.append("{} {}".format(field, direction))

        return ",".join(sort)

    def get_list(self, request, page_num, list_per_page):

        query = CLICKHOUSE_LIST_SQL_TEMPLATE.format(
            where=self._get_where_clause(request),
            order_by=self._get_order_by_clause(request),
            limit=list_per_page,
            offset=((page_num or 1) - 1) * list_per_page,
        )

        response = requests.post(
            CLICKHOUSE_API_URL,
            data=query,
            timeout=CLICKHOUSE_API_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()

        items = [Recipe.build_from(item) for item in result.get("data") or []]

        return {
            "total": result.get("rows_before_limit_at_least", 0),
            "items": items,
        }

    def get_object(self, request, object_id, *args, **kwargs):
        query = CLICKHOUSE_LIST_SQL_TEMPLATE.format(
            # TODO avoid of sql injection!!!
            where="WHERE link = '{}'".format(prevent_injection(object_id)),
            order_by="link asc",
            limit=1,
            offset=0,
        )

        response = requests.post(
            CLICKHOUSE_API_URL,
            data=query,
            timeout=CLICKHOUSE_API_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()

        item = (result.get("data") or [None])[0]

        if not item:
            return

        return Recipe.build_from(item)

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


admin.site.register(Recipe, RecipeAdmin)
