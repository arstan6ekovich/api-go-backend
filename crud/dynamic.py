from rest_framework import serializers
from .models import DynamicData

def get_dynamic_serializer(endpoint):
    class DynamicSerializer(serializers.ModelSerializer):
        class Meta:
            model = DynamicData
            fields = ['data']

        def validate(self, attrs):
            value = attrs.get('data', {})
            errors = {}
            for field, field_type in endpoint.schema.items():
                if field not in value:
                    errors[field] = "Бул талаа талап кылынат"
                else:
                    if field_type == "str" and not isinstance(value[field], str):
                        errors[field] = "Бул талаа текст болушу керек"
                    elif field_type == "int":
                        try:
                            int(value[field])
                        except Exception:
                            errors[field] = "Бул талаа бүтүн сан болушу керек"
                    elif field_type == "bool" and not isinstance(value[field], bool):
                        errors[field] = "Бул талаа true же false болушу керек"
            if errors:
                raise serializers.ValidationError(errors)
            return attrs
    return DynamicSerializer
