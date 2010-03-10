from django.contrib import admin
from django.utils.translation import ugettext as _
from feincms.admin import editor
from zojax.django.categories.forms import CategoryAdminForm
from zojax.django.categories.models import Category


class CategoryInline(admin.TabularInline):
    model = Category
    verbose_name = _("Sub-category")
    verbose_name_plural = _("Sub-categories")
    

class CategoryAdmin(editor.TreeEditor):
    
    form = CategoryAdminForm
    
    list_display = ('title', 'slug',)
    list_filter = ('parent',)
    inlines = [CategoryInline,]



admin.site.register(Category, CategoryAdmin)