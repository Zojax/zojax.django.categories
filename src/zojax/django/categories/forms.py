from django import forms
from django.core.validators import EMPTY_VALUES
from django.forms.models import ModelForm, ModelChoiceField
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from zojax.django.categories.models import Category


class CategoryChoiceField(ModelChoiceField):

    def label_from_instance(self, obj):
        label = super(CategoryChoiceField, self).label_from_instance(obj)
        label = "-" * obj.level + " " + label
        return label


class CategoryAdminForm(ModelForm):

    parent = CategoryChoiceField(Category.objects.all(), label=_("Parent category"), required=False)

    class Meta:
        model = Category
        fields = ('title', 'description', 'parent', 'sites')


class BaseCategoriesTreeWidget(forms.widgets.CheckboxSelectMultiple):

    input_type = "hidden"
    template = "categories/treewidget.html"

    def render(self, name, value, attrs=None):
        if not value:
            value = value
        widget = super(BaseCategoriesTreeWidget, self).render(name, value, attrs=None)
        root_categories = Category.objects.filter(parent=None)
        return mark_safe(render_to_string(self.template, {'widget': widget,
                                                          'name': name,
                                                          'value': value,
                                                          'root_categories': root_categories}))


class CategoriesTreeWidget(BaseCategoriesTreeWidget):

    class Media:
        css = {
          'screen': ('%sjquery/treeview/jquery.treeview.css' % settings.MEDIA_URL, )
        }
        js = (
          '%sjquery/treeview/jquery.treeview.js' % settings.MEDIA_URL,
          '%scategories/treewidget.js' % settings.MEDIA_URL,
        )


class CategoriesTreeAdminWidget(BaseCategoriesTreeWidget):

    class Media:
        css = {
          'screen': ('%sjquery/treeview/jquery.treeview.css' % settings.MEDIA_URL, )
        }
        js = (
          '%sjquery/jquery-1.4.js' % settings.MEDIA_URL,
          '%sjquery/treeview/jquery.treeview.js' % settings.MEDIA_URL,
          '%scategories/treewidget.js' % settings.MEDIA_URL,
        )


class CategoriesField(forms.Field):


    def clean(self, value):
        if self.required and value in EMPTY_VALUES:
            raise forms.ValidationError(self.error_messages['required'])
        try:
            values = Category.objects.filter(pk__in=[int(v) for v in value if v])
        except ValueError:
            raise forms.ValidationError(u"Values must be integers.")
        return values


class CategoriesAdminField(CategoriesField):

    widget = CategoriesTreeAdminWidget


