import random
import numpy as np

import torch
from torchvision.transforms import functional as F


def random_seed(seed=42):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


class TrainTransforms:
    """Standard Augmentation (paired image+mask).

    Includes the required:
    - resize handled in dataset
    - normalization
    - augmentation: flip, rotation, brightness
    """

    def __init__(
        self,
        hflip_prop: float = 0.5,
        rotate_deg: float = 10.0,
        brightness_delta: float = 0.15,
        contrast_delta: float = 0.15,
    ) -> None:
        transforms = []
        if hflip_prop > 0:
            transforms.append(RandomHorizontalFlip(hflip_prop))
        if rotate_deg and rotate_deg > 0:
            transforms.append(RandomRotation(rotate_deg))
        if brightness_delta > 0 or contrast_delta > 0:
            transforms.append(RandomBrightnessContrast(brightness_delta, contrast_delta))
        transforms.extend([PILToTensor(), ConvertImageDtype(torch.float)])
        transforms.append(Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)))
        self.transforms = Compose(transforms)

    def __call__(self, img, target):
        return self.transforms(img, target)


class PILToTensor:
    """Convert PIL image to torch tensor"""

    def __call__(self, image, target):
        image = F.pil_to_tensor(image)
        target = torch.as_tensor(np.array(target), dtype=torch.int64)
        return image, target


class ConvertImageDtype:
    """Convert Image dtype"""

    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, image, target):
        image = F.convert_image_dtype(image, self.dtype)
        return image, target


class Compose:
    """Composing all transforms"""

    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, image, target):
        for t in self.transforms:
            image, target = t(image, target)
        return image, target


class RandomHorizontalFlip:
    """Random horizontal flip"""

    def __init__(self, flip_prob: float = 0.5) -> None:
        self.flip_prob = flip_prob

    def __call__(self, image, target):
        if random.random() < self.flip_prob:
            image = F.hflip(image)
            target = F.hflip(target)
        return image, target


class RandomRotation:
    """Random small rotation (paired)."""

    def __init__(self, max_degrees: float = 10.0) -> None:
        self.max_degrees = float(max_degrees)

    def __call__(self, image, target):
        angle = random.uniform(-self.max_degrees, self.max_degrees)
        image = F.rotate(image, angle=angle, interpolation=F.InterpolationMode.BILINEAR)
        target = F.rotate(target, angle=angle, interpolation=F.InterpolationMode.NEAREST)
        return image, target


class RandomBrightnessContrast:
    """Random brightness/contrast jitter on image only."""

    def __init__(self, brightness_delta: float = 0.15, contrast_delta: float = 0.15) -> None:
        self.brightness_delta = float(brightness_delta)
        self.contrast_delta = float(contrast_delta)

    def __call__(self, image, target):
        b = 1.0 + random.uniform(-self.brightness_delta, self.brightness_delta)
        c = 1.0 + random.uniform(-self.contrast_delta, self.contrast_delta)
        image = F.adjust_brightness(image, b)
        image = F.adjust_contrast(image, c)
        return image, target


class Normalize:
    """Normalize tensor image (expects float CHW in [0,1])."""

    def __init__(self, mean, std) -> None:
        self.mean = mean
        self.std = std

    def __call__(self, image, target):
        image = F.normalize(image, mean=self.mean, std=self.std)
        return image, target
