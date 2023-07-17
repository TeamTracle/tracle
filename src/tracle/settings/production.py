from .base import * # noqa F403

MIDDLEWARE += [  # noqa F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
]
