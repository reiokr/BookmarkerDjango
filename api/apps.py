from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        from django.db.models.signals import post_save

        from api.models import CustomUser

        def addCategory(sender, **kwargs):
            user = kwargs['instance']
            if kwargs['created']:
                user['categories'].append('default')

        return
