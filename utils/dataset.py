import os
import cv2
import numpy as np
from PIL import Image
from torch.utils import data

from utils.general import TrainTransforms


class RoadCrack(data.Dataset):
    def __init__(
            self,
            root: str,
            image_size: int = 448,
            transforms: TrainTransforms = TrainTransforms,
            mask_suffix: str = "_mask"
    ) -> None:
        self.root = root
        self.image_size = image_size
        self.mask_suffix = mask_suffix
        self.images_dir = os.path.join(self.root, "images")
        self.masks_dir = os.path.join(self.root, "masks")
        
        # Native Kaggle dataset support (flat folder)
        if not os.path.exists(self.images_dir) or not os.path.exists(self.masks_dir):
            self.images_dir = self.root
            self.masks_dir = self.root
            
        # Only collect actual image files, avoid masks if they are in the same folder
        self.filenames = []
        for f in os.listdir(self.images_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.bmp', '.tif')):
                self.filenames.append(os.path.splitext(f)[0])
                
        if not self.filenames:
            raise FileNotFoundError(f"No image files found in {self.images_dir}")
        self.transforms = transforms()

    def __len__(self) -> int:
        return len(self.filenames)

    def __getitem__(self, idx):
        filename = self.filenames[idx]

        # image path
        image_path = _find_by_stem(self.images_dir, filename, exts=(".jpg", ".jpeg", ".bmp", ".tif"))
        # mask path (Kaggle usually provides masks as .png)
        mask_path = _find_by_stem(self.masks_dir, filename + self.mask_suffix, exts=(".png",)) or \
                    _find_by_stem(self.masks_dir, filename, exts=(".png",))
                    
        if image_path is None:
            raise FileNotFoundError(f"Image not found for stem '{filename}' in {self.images_dir}")
        if mask_path is None:
            raise FileNotFoundError(
                f"Mask (.png) not found for stem '{filename}' in {self.masks_dir}"
            )

        # image load
        image = Image.open(image_path)
        mask = Image.open(mask_path)

        mask = to_binary(mask)

        assert image.size == mask.size, f"`image`: {image.size} and `mask`: {mask.size} are not the same"

        # TODO: letterbox or some other resizing methods should be used if image is not square.
        # resize input
        image = image.resize((self.image_size, self.image_size))
        mask = mask.resize((self.image_size, self.image_size))

        # transform
        if self.transforms is not None:
            image, mask = self.transforms(image, mask)

        return image, mask


def to_binary(mask_image):
    # Convert PIL Image to numpy array
    mask_array = np.array(mask_image)

    # Apply threshold directly to create a binary image with values 0 and 255
    _, binary_mask = cv2.threshold(mask_array, 127, 255, cv2.THRESH_BINARY)
    binary_mask = binary_mask.astype(np.uint8) / 255

    # Convert numpy array back to PIL Image, already in binary format
    binary_mask = Image.fromarray(binary_mask)

    return binary_mask


def _find_by_stem(folder: str, stem: str, exts: tuple = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")) -> str | None:
    for ext in exts:
        p = os.path.join(folder, stem + ext)
        if os.path.exists(p):
            return p
    # fallback: any file starting with stem (rare datasets)
    try:
        for name in os.listdir(folder):
            if os.path.splitext(name)[0] == stem:
                return os.path.join(folder, name)
    except FileNotFoundError:
        return None
    return None
