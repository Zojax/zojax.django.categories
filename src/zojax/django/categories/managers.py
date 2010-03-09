from django.contrib.contenttypes.models import ContentType
from django.db import models
from zojax.django.categories.models import Category, CategorizedItem


class ModelCategoryManager(models.Manager):
    """
    A manager for retrieving categories for a particular model.
    """
    def get_query_set(self):
        ctype = ContentType.objects.get_for_model(self.model)
        return Category.objects.filter(
            items__content_type__pk=ctype.pk).distinct()


class ModelCategorizedItemManager(models.Manager):
    """
    A manager for retrieving model instances based on their categories.
    """
    def related_to(self, obj, queryset=None, num=None):
        if queryset is None:
            return CategorizedItem.objects.get_related(obj, self.model, num=num)
        else:
            return CategorizedItem.objects.get_related(obj, queryset, num=num)

    def with_all(self, categories, queryset=None):
        if queryset is None:
            return CategorizedItem.objects.get_by_model(self.model, categories)
        else:
            return CategorizedItem.objects.get_by_model(queryset, categories)

    def with_any(self, categories, queryset=None):
        if queryset is None:
            return CategorizedItem.objects.get_union_by_model(self.model, categories)
        else:
            return CategorizedItem.objects.get_union_by_model(queryset, categories)


class CategoryDescriptor(object):
    """
    A descriptor which provides access to a ``ModelCategoryManager`` for
    model classes and simple retrieval, updating and deletion of categories
    for model instances.
    """
    def __get__(self, instance, owner):
        if not instance:
            category_manager = ModelCategoryManager()
            category_manager.model = owner
            return category_manager
        else:
            return Category.objects.get_for_object(instance)

    def __set__(self, instance, value):
        Category.objects.update_categories(instance, value)

    def __delete__(self, instance):
        Category.objects.update_categories(instance, None)
