from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from .models import Profile
from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.http import Http404
from .models import Endpoint, DynamicData, UploadedImage
from .serializers import EndpointSerializer, DynamicDataSerializer, get_dynamic_serializer, UploadedImageSerializer
from .pagination import CustomPagination
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema

@api_view(['POST'])
@permission_classes([AllowAny])
def social_register(request):
    email = request.data.get('email')
    name = request.data.get('name', '')
    last_name = request.data.get('last_name', '')
    image_url = request.data.get('image', '')

    if not email:
        return Response({"error": "Email required"}, status=400)

    # Эгер last_name келбесе → name бөлөбүз
    if not last_name and name:
        parts = name.split()
        name = parts[0] if len(parts) > 0 else ''
        last_name = parts[1] if len(parts) > 1 else ''

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'first_name': name,
            'last_name': last_name
        }
    )

    if not created:
        user.first_name = name
        user.last_name = last_name
        user.save()

    profile, _ = Profile.objects.get_or_create(user=user)

    if image_url:
        profile.image = image_url
        profile.save()

    serializer = UserSerializer(user)

    refresh = RefreshToken.for_user(user)

    return Response({
        "user": serializer.data,
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)



class UserProfile(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class EndpointListCreateView(generics.ListCreateAPIView):
    serializer_class = EndpointSerializer
    permission_classes = [IsAuthenticated]  # Защищено — нужен аутентифицированный пользователь

    def get_queryset(self):
        return Endpoint.objects.filter(user=self.request.user, is_trashed=False).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        if Endpoint.objects.filter(user=user).count() >= 30:
            raise serializers.ValidationError("Сиз 30дан ашык endpoint түзө албайсыз.")
        serializer.save(user=user)


class DynamicCRUDView(viewsets.ViewSet):
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_endpoint(self, token, resource):
        try:
            return Endpoint.objects.get(token=token, name=resource, is_trashed=False)
        except Endpoint.DoesNotExist:
            raise Http404("Invalid token or resource")

    def list(self, request, token, resource):
        endpoint = self.get_endpoint(token, resource)
        queryset = DynamicData.objects.filter(endpoint=endpoint).order_by('created_at')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = DynamicDataSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def create(self, request, token, resource):
        endpoint = self.get_endpoint(token, resource)
        SerializerClass = get_dynamic_serializer(endpoint)
        serializer = SerializerClass(data={"data": request.data})
        if serializer.is_valid():
            serializer.save(endpoint=endpoint)
            return Response(DynamicDataSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, token, resource, id=None):
        endpoint = self.get_endpoint(token, resource)
        try:
            item = DynamicData.objects.get(endpoint=endpoint, id=id)
        except DynamicData.DoesNotExist:
            raise Http404("Not found")
        return Response(DynamicDataSerializer(item).data)

    def update(self, request, token, resource, id=None):
        endpoint = self.get_endpoint(token, resource)
        try:
            item = DynamicData.objects.get(endpoint=endpoint, id=id)
        except DynamicData.DoesNotExist:
            raise Http404("Not found")
        SerializerClass = get_dynamic_serializer(endpoint)
        serializer = SerializerClass(item, data={"data": request.data})
        if serializer.is_valid():
            serializer.save()
            return Response(DynamicDataSerializer(item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, token, resource, id=None):
        endpoint = self.get_endpoint(token, resource)
        try:
            item = DynamicData.objects.get(endpoint=endpoint, id=id)
        except DynamicData.DoesNotExist:
            raise Http404("Not found")
        SerializerClass = get_dynamic_serializer(endpoint)
        serializer = SerializerClass(item, data={"data": request.data}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(DynamicDataSerializer(item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, token, resource, id=None):
        endpoint = self.get_endpoint(token, resource)
        try:
            item = DynamicData.objects.get(endpoint=endpoint, id=id)
        except DynamicData.DoesNotExist:
            raise Http404("Not found")
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_endpoint_data(request, id):
    try:
        endpoint = Endpoint.objects.get(id=id, user=request.user)
        DynamicData.objects.filter(endpoint=endpoint).delete()
        return Response({"message": "Маалыматтар өчүрүлдү ✅"}, status=200)
    except Endpoint.DoesNotExist:
        return Response({"error": "Endpoint табылган жок"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trash_endpoint(request, id):
    try:
        endpoint = Endpoint.objects.get(id=id, user=request.user)
        endpoint.is_trashed = True
        endpoint.save()
        return Response({"message": "Trash'ка жөнөтүлдү 🗑️"}, status=200)
    except Endpoint.DoesNotExist:
        return Response({"error": "Endpoint табылган жок"}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trashed_endpoints(request):
    endpoints = Endpoint.objects.filter(user=request.user, is_trashed=True).order_by('-created_at')
    serializer = EndpointSerializer(endpoints, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recover_endpoint(request, id):
    try:
        endpoint = Endpoint.objects.get(id=id, user=request.user, is_trashed=True)
        endpoint.is_trashed = False
        endpoint.save()
        return Response({"message": "Endpoint калыбына келтирилди ✅"}, status=200)
    except Endpoint.DoesNotExist:
        return Response({"error": "Endpoint табылган жок"}, status=404)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_endpoint(request, id):
    try:
        endpoint = Endpoint.objects.get(id=id, user=request.user, is_trashed=True)
        endpoint.delete()
        return Response({"message": "Endpoint толук өчүрүлдү 🗑️"}, status=200)
    except Endpoint.DoesNotExist:
        return Response({"error": "Endpoint табылган жок"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trash_all_endpoints(request):
    endpoints = Endpoint.objects.filter(user=request.user, is_trashed=False)
    count = endpoints.count()
    if count == 0:
        return Response({"message": "Trash'ка жөнөтө турган Endpoint жок"}, status=404)
    endpoints.update(is_trashed=True)
    return Response({"message": f"{count} endpoint Trash'ка жөнөтүлдү 🗑️"}, status=200)




class UploadImageView(viewsets.ModelViewSet):
    queryset = UploadedImage.objects.all()
    serializer_class = UploadedImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UploadedImageSerializer)
    def upload_single(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(request_body=UploadedImageSerializer)
    def upload_multiple(self, request, *args, **kwargs):
        files = request.FILES.getlist('image')
        uploaded_items = []

        for file in files:
            serializer = self.get_serializer(data={'image': file})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            uploaded_items.append(serializer.data)

        return Response(uploaded_items, status=status.HTTP_201_CREATED)
