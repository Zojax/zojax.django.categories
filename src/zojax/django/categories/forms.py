from django import forms
from django.core.validators import EMPTY_VALUES
from django.utils.safestring import mark_safe
from zojax.django.categories.models import Category
from django.template.loader import render_to_string


class CategoriesTreeWidget(forms.widgets.CheckboxSelectMultiple):
    
    input_type = "hidden"
    template = "categories/treewidget.html" 
    
    def render(self, name, value, attrs=None):
        if not value:
            value = value
        widget = super(CategoriesTreeWidget, self).render(name, value, attrs=None)
        root_categories = Category.objects.filter(parent=None)
        return mark_safe(render_to_string(self.template, {'widget': widget,
                                                          'name': name,
                                                          'value': value,
                                                          'root_categories': root_categories}))


class CategoriesField(forms.Field):
    
    widget = CategoriesTreeWidget
    
    def clean(self, value):        
        if self.required and value in EMPTY_VALUES:
            raise forms.ValidationError(self.error_messages['required'])
        try:
            values = Category.objects.filter(pk__in=[int(v) for v in value if v])
        except ValueError:
            raise forms.ValidationError(u"Values must be integers.")
        return values


    