from django.core.exceptions import ImproperlyConfigured

import pytest
from django.test import RequestFactory
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema

from rest_polymorphic.serializers import PolymorphicSerializer

from tests.models import BlogBase, BlogOne, BlogTwo
from tests.serializers import BlogPolymorphicSerializer

pytestmark = pytest.mark.django_db


def create_request(path):
    factory = RequestFactory()
    request = Request(factory.get(path))
    return request


def create_view(view_cls, method, request):
    generator = SchemaGenerator()
    view = generator.create_view(view_cls.as_view(), method, request)
    return view


class TestPolymorphicSerializerAutoSchema:

    def test_response_body_generation(self):
        path = '/'
        method = 'POST'

        class View(generics.GenericAPIView):
            serializer_class = BlogPolymorphicSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector.get_responses(path, method)
        assert responses['201']['content']['application/json']['schema']['$ref'] == '#/components/schemas/BlogPolymorphic'

        components = inspector.get_components(path, method)
        comp_bp = components['BlogPolymorphic']
        assert 'oneOf' in comp_bp
        assert len(comp_bp['oneOf']) == len(BlogPolymorphicSerializer.model_serializer_mapping)
        for comp in comp_bp['oneOf']:
            assert comp_bp['discriminator'] in comp['properties']
            assert comp_bp['discriminator'] in comp['required']
        assert comp_bp['discriminator'] == BlogPolymorphicSerializer.resource_type_field_name
