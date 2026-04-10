from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Endpoint, DynamicData, UploadedImage


class UserSerializer(serializers.ModelSerializer):
    image = serializers.CharField(source='profile.image', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'image']



class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = ['id', 'name', 'token', 'schema', 'created_at', 'updated_at']
        read_only_fields = ['token', 'created_at', 'updated_at']


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


class DynamicDataSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source='serial_number', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M:%S %z", read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', format="%Y-%m-%d %H:%M:%S %z", read_only=True)

    class Meta:
        model = DynamicData
        fields = ['_id', 'data', 'createdAt', 'updatedAt']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        data = ret.pop('data')
        ret.update(data)
        return ret



class UploadedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ['image', 'uploaded_at']
