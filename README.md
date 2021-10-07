
<div align="center">
 <p><h1>django-admin-data-from-external-service</h1> </p>
  <p><strong>Helpers to extend Django Admin with data from external service with minimal hacks</strong></p>
  <p></p>
</div>

[Live demo](https://dadfes.herokuapp.com/) with [sources](https://github.com/estin/django-admin-data-from-external-service/tree/master/demo) on [Heroku](https://heroku.com) free quota (please be patient, it will take some time for the app to wake up)
 - [view](http://dadfes.herokuapp.com/github/repository/) Github repository of Django org ([sources](https://github.com/estin/django-admin-data-from-external-service/tree/master/demo/github/models.py)), may appear api rate limit error
 - [view](http://dadfes.herokuapp.com/clickhouse/recipe/) recipes from ClickHouse [playground](https://clickhouse.com/docs/en/getting-started/example-datasets/recipes/) ([sources](https://github.com/estin/django-admin-data-from-external-service/tree/master/demo/clickhouse/models.py))

Main features:
 - reuse Django Admin layout to simplify customization of viewing and managing external data (list/view/filter+search/ordering)
 - datasource agnostic
 - django2.x and django3.x support

## How it works

Used custom ChangeList to determine method to pull external data and mock paginator behaviour.

## Example

```python
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
        data =  {
            'total': 1,
            'users': [
                {'id': 1, 'username': 'User1'},
            ]
        }

        items = [ExternalUser(**i) for i in data.get("users") or []]

        return {
            "total": data.get("total") or 0,
            "items": items,
        }

    # other django admin customization

admin.site.register(ExternalUser, ExternalUserAdmin)
```

## License

This project is licensed under

* MIT license ([LICENSE](LICENSE) or [http://opensource.org/licenses/MIT](http://opensource.org/licenses/MIT))
