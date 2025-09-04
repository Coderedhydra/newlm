from .base import BackgroundProvider
from .gradient import GradientBackgroundProvider
from .image_dir import ImageDirectoryBackgroundProvider

PROVIDERS = {
    "gradient": GradientBackgroundProvider,
    "image_dir": ImageDirectoryBackgroundProvider,
}

