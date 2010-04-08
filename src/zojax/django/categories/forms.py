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
        fields = ('title', 'parent')        
    

class CategoriesTreeWidget(forms.widgets.CheckboxSelectMultiple):
    
    input_type = "hidden"
    template = "categories/treewidget.html" 

    class Media:
                css = {
                        'all': ('%sjquery/treeview/jquery.treeview.css' % settings.MEDIA_URL,)
                }
                js = ('%sjquery/treeview/jquery.treeview.js' % settings.MEDIA_URL,
                      '%scategories/treewidget.js' % settings.MEDIA_URL,
                )
        
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


    