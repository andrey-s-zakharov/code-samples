"""
These functions allows saving nested data in Django Rest Framework serializers.
Almost every complicated serializer has nested data which we must convert and save in models (DB).
Functions help create, update and delete nested and M2M objects in correspond serializer methods.
"""

def update_object_with_data(instance, data):
    for attr, value in data.items():
        setattr(instance, attr, value)
    instance.save()
    return instance


def create_objects_with_data(related_data, model, instance, instance_str):
    """ Create new objects as nested objects """
    for dt in related_data:
        dt[instance_str] = instance
        model.objects.create(**dt)


def create_or_update_nested_object(child_data, model, parent_param, instance):
    """ Update object with id or create new one """
    child_id = child_data.get('id')
    child_data.update({parent_param: instance})
    if child_id:
        child_obj = model.objects.filter(id=child_id).first()
        if child_obj:
            return update_object_with_data(instance=child_obj, data=child_data)
    return model.objects.create(**child_data)


def create_or_update_m2m_object(child_data, model, parent_param, m2m_manager, instance):
    """ Create or update nested object and add it to m2m manager """
    child_id = child_data.get('id')
    child_data.update({parent_param: instance})
    if child_id:
        child_obj = model.objects.filter(id=child_id).first()
        if child_obj:
            return update_object_with_data(instance=child_obj, data=child_data)
    child_obj = model.objects.create(**child_data)
    m2m_manager.add(child_obj)
    return child_obj


def delete_not_included_objects(objects, parent_param, instance):
    """ Delete objects which not included in incoming data """
    object_ids = [item.get('id') for item in objects]
    for obj in getattr(instance, parent_param).all():
        if obj.id not in object_ids:
            obj.delete()


"""
For example we have Course model with CoursePriceRange reverse related field.
So 'create' method is serailizer looks like:
"""
def create(self, validated_data):
    price_ranges = validated_data.pop('price_ranges', [])
    course = Course.objects.create(**validated_data)
    create_objects_with_data(
        related_data=price_ranges,
        model=CoursePriceRange,
        instance=course,
        instance_str='course')
    return course

""" 'update' method of this serializer looks like: """
def update(self, instance, validated_data):
    price_ranges = validated_data.pop('price_ranges', [])
    delete_not_included_objects(
        objects=price_ranges,
        parent_param='price_ranges',
        instance=instance)
    instance = update_object_with_data(instance=instance, data=validated_data)
    for price_range in price_ranges:
        create_or_update_nested_object(
            child_data=price_range,
            model=CoursePriceRange,
            parent_param='course',
            instance=instance)
    instance.save()
    return instance
