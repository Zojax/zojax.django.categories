from django.contrib import admin
from django.db import models
from django.contrib.admin.filterspecs import FilterSpec
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ChangeList
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from feincms.admin import editor
from zojax.django.categories.forms import CategoryAdminForm
from zojax.django.categories.models import Category, CategorizedItem


class CategoryInline(admin.TabularInline):
    model = Category
    verbose_name = _("Sub-category")
    verbose_name_plural = _("Sub-categories")
    extra = 0
    

class CategoryAdmin(editor.TreeEditor):
    
    form = CategoryAdminForm
    
    list_display = ('title', 'slug',)
    list_filter = ('parent',)
    inlines = [CategoryInline, ]



admin.site.register(Category, CategoryAdmin)


class CategoriesFilterSpec(FilterSpec):

    def __init__(self, f, request, params, model, model_admin, field_path=None):
        self.field = f
        self.params = params
        self.field_path = field_path
        if field_path is None:
            if isinstance(f, models.related.RelatedObject):
                self.field_path = f.var_name
            else:
                self.field_path = getattr(f,'name', None)
        self.lookup_kwarg = "category"
        self.model = model
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)
    
    def title(self):
        return _(u"category")
    
    def choices(self, cl):
        yield {'selected': self.lookup_val is None,
               'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
               'display': _('Any')}
        for category in Category.objects.usage_for_model(self.model, min_count=1):
            k = category.id
            v = category.title
            yield {'selected': smart_unicode(k) == self.lookup_val,
                    'query_string': cl.get_query_string({self.lookup_kwarg: k}),
                    'display': v}
        


class ChangeListWithCategories(ChangeList):
    
    def __init__(self, *args, **kwargs):
        self.category = None
        super(ChangeListWithCategories, self).__init__(*args, **kwargs)

    def get_filters(self, request):
        filter_specs, has_filters = super(ChangeListWithCategories, self).get_filters(request)
        filter_specs.append(CategoriesFilterSpec(None, request, self.params, self.model, self.model_admin))
        return filter_specs, bool(filter_specs)
        
    def get_query_set(self):
        
        if "category" in self.params:
            self.category = self.params["category"]
            del self.params["category"]
            
        qs = super(ChangeListWithCategories, self).get_query_set()
        if self.category is None:
            return qs
        
        try:
            category = Category.objects.get(pk=int(self.category))
        except:
            raise IncorrectLookupParameters
    
        return CategorizedItem.objects.get_union_by_model(qs, [category])
