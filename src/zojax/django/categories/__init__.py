

class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model more than once.
    """
    pass


registry = []


def register(model, category_descriptor_attr='categories',
             categorized_item_manager_attr='categorized'):
    """
    Sets the given model class up for working with categories.
    """

    from zojax.django.categories.managers import ModelCategorizedItemManager, CategoryDescriptor

    if model in registry:
        raise AlreadyRegistered("The model '%s' has already been "
            "registered." % model._meta.object_name)
    if hasattr(model, category_descriptor_attr):
        raise AttributeError("'%s' already has an attribute '%s'. You must "
            "provide a custom category_descriptor_attr to register." % (
                model._meta.object_name,
                category_descriptor_attr,
            )
        )
    if hasattr(model, categorized_item_manager_attr):
        raise AttributeError("'%s' already has an attribute '%s'. You must "
            "provide a custom categorized_item_manager_attr to register." % (
                model._meta.object_name,
                categorized_item_manager_attr,
            )
        )

    # Add category descriptor
    setattr(model, category_descriptor_attr, CategoryDescriptor())

    # Add custom manager
    ModelCategorizedItemManager().contribute_to_class(model, categorized_item_manager_attr)

    # Finally register in registry
    registry.append(model)
