"""
Tests for registering a device
"""
from django.test import TestCase
from uuid import uuid4

# Third party
import responses

# Local stuff
from .factories import TestUserFactory, request_register_callback
from push_notifications.services.zeropush import ZEROPUSH_REGISTER_URL
from push_notifications.models import PushDevice
from push_notifications.utils import register_push_device


class RegisterDeviceTests(TestCase):
    def _create_token(self):
        return uuid4()

    def _create_user(self):
        return TestUserFactory.create()

    @responses.activate
    def test_register_device_manager(self):
        """
        Test if register_device() on the manager works as expected
        """
        responses.add_callback(
            responses.POST, ZEROPUSH_REGISTER_URL,
            callback=request_register_callback,
            content_type='application/json',
        )

        user = TestUserFactory.create()
        device = PushDevice.objects.register_push_device(
            user, self._create_token())

        assert device is not None
        assert device.user.pk == user.pk

    @responses.activate
    def test_register_device_manager_notify_types(self):
        """
        Test if manager.register_push_device() accepts notify_types
        """
        responses.add_callback(
            responses.POST, ZEROPUSH_REGISTER_URL,
            callback=request_register_callback,
            content_type='application/json',
        )

        user = self._create_user()
        device = PushDevice.objects.register_push_device(
            user, self._create_token(), notify_types='likes')

        notification = device.notification_settings.first()
        assert device.notification_settings.count() == 1
        assert notification.name == 'likes'

        device = PushDevice.objects.register_push_device(
            user, self._create_token(), notify_types=['likes', 'comments'])

        assert device.notification_settings.count() == 2

        notification_likes = device.notification_settings.filter(name='likes').first()
        assert notification_likes.send is True

        notification_comments = device.notification_settings.filter(name='comments').first()
        assert notification_comments.send is True

    @responses.activate
    def test_register_device_service(self):
        """
        Tests if register_push_device in services works as expected
        """
        responses.add_callback(
            responses.POST, ZEROPUSH_REGISTER_URL,
            callback=request_register_callback,
            content_type='application/json',
        )

        user = self._create_user()
        device = register_push_device(user, self._create_token())

        assert device is not None
        assert device.user.pk == user.pk

    @responses.activate
    def test_register_device_token_duplicate_removed(self):
        """
        Test if other push devices with the same token are getting
        deleted.
        """
        responses.add_callback(
            responses.POST, ZEROPUSH_REGISTER_URL,
            callback=request_register_callback,
            content_type='application/json',
        )

        user = self._create_user()
        token = self._create_token()
        PushDevice.objects.register_push_device(
            user, token, notify_types='likes')

        # Create other user
        other_user = self._create_user()
        PushDevice.objects.register_push_device(
            other_user, token)

        assert PushDevice.objects.filter(token=token).count() == 1

    @responses.activate
    def test_register_device_service_notify_types(self):
        """
        Tests if register_push_device in services workw with extra
        notice_types
        """
        responses.add_callback(
            responses.POST, ZEROPUSH_REGISTER_URL,
            callback=request_register_callback,
            content_type='application/json',
        )

        user = self._create_user()
        device = register_push_device(user, self._create_token(), notice_types='likes')

        # Check if notice_types has 'likes' in it
        notification = device.notification_settings.first()
        assert device.notification_settings.count() == 1
        assert notification.name == 'likes'
        assert notification.send is True

        # Test with multiple notice_types
        device = register_push_device(user, self._create_token(),
                                      notice_types=['likes', 'comments'])

        # Check if notice_types has 'likes' and 'comments'
        assert device.notification_settings.count() == 2

        notification_likes = device.notification_settings.filter(name='likes').first()
        assert notification_likes.send is True

        notification_comments = device.notification_settings.filter(name='comments').first()
        assert notification_comments.send is True
