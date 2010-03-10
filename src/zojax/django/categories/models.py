from autoslug.fields import AutoSlugField
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from zojax.django.categories.utils import get_queryset_and_model
import mptt


qn = connection.ops.quote_name


class CategoryManager(models.Manager):
    
    def update_categories(self, obj, categories):
        """
        Update categories associated with an object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        current_categories = list(self.filter(items__content_type__pk=ctype.pk,
                                  items__object_id=obj.pk))

        # Remove categories which no longer apply
        categories_for_removal = [category for category in current_categories \
                                  if category not in categories]
        if len(categories_for_removal):
            CategorizedItem._default_manager.filter(content_type__pk=ctype.pk,
                                                           object_id=obj.pk,
                                                           category__in=categories_for_removal).delete()
        for category in categories:
            if category not in current_categories:
                CategorizedItem._default_manager.create(category=category, object=obj)

    def add_category(self, obj, category):
        """
        Associates the given object with a category.
        """
        ctype = ContentType.objects.get_for_model(obj)
        CategorizedItem._default_manager.get_or_create(
            category=category, content_type=ctype, object_id=obj.pk)

    def get_for_object(self, obj):
        """
        Create a queryset matching all categories associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(items__content_type__pk=ctype.pk,
                           items__object_id=obj.pk)


class Category(models.Model):
    
    title = models.CharField(max_length=200, verbose_name=_(u"Title"))
    slug = AutoSlugField(populate_from='title', verbose_name=_(u"Slug"))
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_(u"Parent category"))
    
    objects = CategoryManager()
    
    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _(u"Category")
        verbose_name_plural = _(u"Categories")
        
    def __unicode__(self):
        return self.title


mptt.register(Category, order_insertion_by=['title'])


class CategorizedItemManager(models.Manager):
    
    def get_by_model(self, queryset_or_model, categories):
        """
        Create a ``QuerySet`` containing instances of the specified
        model associated with a given category or list of categories.
        """
        categories_count = len(categories)
        if categories_count == 0:
            # No existing categories were given
            queryset, model = get_queryset_and_model(queryset_or_model)
            return model._default_manager.none()
        elif categories_count == 1:
            # Optimisation for single category - fall through to the simpler
            # query below.
            category = categories[0]
        else:
            return self.get_intersection_by_model(queryset_or_model, categories)

        queryset, model = get_queryset_and_model(queryset_or_model)
        content_type = ContentType.objects.get_for_model(model)
        opts = self.model._meta
        categorized_item_table = qn(opts.db_table)
        return queryset.extra(
            tables=[opts.db_table],
            where=[
                '%s.content_type_id = %%s' % categorized_item_table,
                '%s.category_id = %%s' % categorized_item_table,
                '%s.%s = %s.object_id' % (qn(model._meta.db_table),
                                          qn(model._meta.pk.column),
                                          categorized_item_table)
            ],
            params=[content_type.pk, category.pk],
        )

    def get_intersection_by_model(self, queryset_or_model, categories):
        """
        Create a ``QuerySet`` containing instances of the specified
        model associated with *all* of the given list of categories.
        """
        category_count = len(categories)
        queryset, model = get_queryset_and_model(queryset_or_model)

        if not category_count:
            return model._default_manager.none()

        model_table = qn(model._meta.db_table)
        # This query selects the ids of all objects which have all the
        # given categories.
        query = """
        SELECT %(model_pk)s
        FROM %(model)s, %(categorized_item)s
        WHERE %(categorized_item)s.content_type_id = %(content_type_id)s
          AND %(categorized_item)s.category_id IN (%(category_id_placeholders)s)
          AND %(model_pk)s = %(categorized_item)s.object_id
        GROUP BY %(model_pk)s
        HAVING COUNT(%(model_pk)s) = %(category_count)s""" % {
            'model_pk': '%s.%s' % (model_table, qn(model._meta.pk.column)),
            'model': model_table,
            'categorized_item': qn(self.model._meta.db_table),
            'content_type_id': ContentType.objects.get_for_model(model).pk,
            'category_id_placeholders': ','.join(['%s'] * category_count),
            'category_count': category_count,
        }

        cursor = connection.cursor()
        cursor.execute(query, [category.pk for category in categories])
        object_ids = [row[0] for row in cursor.fetchall()]
        if len(object_ids) > 0:
            return queryset.filter(pk__in=object_ids)
        else:
            return model._default_manager.none()

    def get_union_by_model(self, queryset_or_model, categories):
        """
        Create a ``QuerySet`` containing instances of the specified
        model associated with *any* of the given list of categories.
        """
        category_count = len(categories)
        queryset, model = get_queryset_and_model(queryset_or_model)

        if not category_count:
            return model._default_manager.none()

        model_table = qn(model._meta.db_table)
        # This query selects the ids of all objects which have any of
        # the given categories.
        query = """
        SELECT %(model_pk)s
        FROM %(model)s, %(categorized_item)s
        WHERE %(categorized_item)s.content_type_id = %(content_type_id)s
          AND %(categorized_item)s.category_id IN (%(category_id_placeholders)s)
          AND %(model_pk)s = %(categorized_item)s.object_id
        GROUP BY %(model_pk)s""" % {
            'model_pk': '%s.%s' % (model_table, qn(model._meta.pk.column)),
            'model': model_table,
            'categorized_item': qn(self.model._meta.db_table),
            'content_type_id': ContentType.objects.get_for_model(model).pk,
            'category_id_placeholders': ','.join(['%s'] * category_count),
        }

        cursor = connection.cursor()
        cursor.execute(query, [category.pk for category in categories])
        object_ids = [row[0] for row in cursor.fetchall()]
        if len(object_ids) > 0:
            return queryset.filter(pk__in=object_ids)
        else:
            return model._default_manager.none()

    def get_related(self, obj, queryset_or_model, num=None):
        """
        Retrieve a list of instances of the specified model which share
        categories with the model instance ``obj``, ordered by the number of
        shared categories in descending order.

        If ``num`` is given, a maximum of ``num`` instances will be
        returned.
        """
        queryset, model = get_queryset_and_model(queryset_or_model)
        model_table = qn(model._meta.db_table)
        content_type = ContentType.objects.get_for_model(obj)
        related_content_type = ContentType.objects.get_for_model(model)
        query = """
        SELECT %(model_pk)s, COUNT(related_categorized_item.object_id) AS %(count)s
        FROM %(model)s, %(categorized_item)s, %(category)s, %(categorized_item)s related_categorized_item
        WHERE %(categorized_item)s.object_id = %%s
          AND %(categorized_item)s.content_type_id = %(content_type_id)s
          AND %(category)s.id = %(categorized_item)s.category_id
          AND related_categorized_item.content_type_id = %(related_content_type_id)s
          AND related_categorized_item.category_id = %(categorized_item)s.category_id
          AND %(model_pk)s = related_categorized_item.object_id"""
        if content_type.pk == related_content_type.pk:
            # Exclude the given instance itself if determining related
            # instances for the same model.
            query += """
          AND related_categorized_item.object_id != %(categorized_item)s.object_id"""
        query += """
        GROUP BY %(model_pk)s
        ORDER BY %(count)s DESC
        %(limit_offset)s"""
        query = query % {
            'model_pk': '%s.%s' % (model_table, qn(model._meta.pk.column)),
            'count': qn('count'),
            'model': model_table,
            'categorized_item': qn(self.model._meta.db_table),
            'category': qn(self.model._meta.get_field('category').rel.to._meta.db_table),
            'content_type_id': content_type.pk,
            'related_content_type_id': related_content_type.pk,
            # Hardcoding this for now just to get tests working again - this
            # should now be handled by the query object.
            'limit_offset': num is not None and 'LIMIT %s' or '',
        }

        cursor = connection.cursor()
        params = [obj.pk]
        if num is not None:
            params.append(num)
        cursor.execute(query, params)
        object_ids = [row[0] for row in cursor.fetchall()]
        if len(object_ids) > 0:
            # Use in_bulk here instead of an id__in lookup, because id__in would
            # clobber the ordering.
            object_dict = queryset.in_bulk(object_ids)
            return [object_dict[object_id] for object_id in object_ids \
                    if object_id in object_dict]
        else:
            return []


class CategorizedItem(models.Model):
    category = models.ForeignKey(Category, verbose_name=_('category'), related_name='items')
    content_type = models.ForeignKey(ContentType, verbose_name=_('content type'))
    object_id    = models.PositiveIntegerField(_('object id'), db_index=True)
    object       = generic.GenericForeignKey('content_type', 'object_id')

    objects = CategorizedItemManager()

    class Meta:
        # Enforce unique category association per object
        unique_together = (('category', 'content_type', 'object_id'),)
        verbose_name = _('categorized item')
        verbose_name_plural = _('categorized items')

    def __unicode__(self):
        return u'%s [%s]' % (self.object, self.category)
        
