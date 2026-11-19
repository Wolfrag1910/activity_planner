"""
Profile photos: checked, turned the right way up, shrunk, and stripped of hidden
data (phone photos can carry the GPS location where they were taken).
"""

import uuid
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_MB = 15
LONGEST_SIDE = 600  # plenty for an avatar, small enough to load fast on phones

# Refuse absurdly large images (a classic way to crash image libraries).
Image.MAX_IMAGE_PIXELS = 60_000_000


def prepare_profile_photo(upload):
    """Return a clean JPEG ready to save, or raise ValidationError with a friendly message."""
    if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(_("That photo is too big. Please choose one under %(mb)s MB.") % {"mb": MAX_UPLOAD_MB})
    try:
        with Image.open(upload) as image:
            image = ImageOps.exif_transpose(image)  # phones store rotation separately
            image = image.convert("RGB")
            image.thumbnail((LONGEST_SIDE, LONGEST_SIDE))
            buffer = BytesIO()
            # Saving fresh without the original metadata drops location and camera details.
            image.save(buffer, format="JPEG", quality=85, optimize=True)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise ValidationError(_("That file isn't a photo we can read. Try a JPG or PNG."))
    return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4().hex}.jpg")
