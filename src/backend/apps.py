from django.apps import AppConfig


class BackendConfig(AppConfig):
    name = "backend"

    def ready(self):
        import backend.signals
        from actstream import registry

        registry.register(self.get_model("User"))
        registry.register(self.get_model("Channel"))
        registry.register(self.get_model("Video"))
        registry.register(self.get_model("Comment"))
