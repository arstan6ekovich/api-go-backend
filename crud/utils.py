from django.db import models

_dynamic_models_cache = {}

def get_dynamic_model(name):
    if name in _dynamic_models_cache:
        return _dynamic_models_cache[name]

    class Meta:
        app_label = 'endpoints'

    attrs = {
        '__module__': 'endpoints.models',
        'Meta': Meta,
        'id': models.AutoField(primary_key=True)
    }

    model = type(name.capitalize(), (models.Model,), attrs)
    _dynamic_models_cache[name] = model
    return model
