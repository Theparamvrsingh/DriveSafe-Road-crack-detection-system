import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np

import sys
from tqdm import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.unet import UNet

EPOCHS = 30
BATCH_SIZE = 8
LR = 1e-3
IMAGE_SIZE = 256

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'segmentation')
WEIGHTS_DIR = os.path.join(BASE_DIR, 'weights')
os.makedirs(WEIGHTS_DIR, exist_ok=True)

class CrackDataset(Dataset):
    def __init__(self, split):
        self.split_dir = os.path.join(DATA_DIR, split)
        self.images_dir = os.path.join(self.split_dir, 'images')
        self.masks_dir = os.path.join(self.split_dir, 'masks')
        
        # Kaggle CRACK500 format ('traindata' instead of 'train/images')
        kaggle_dir = os.path.join(DATA_DIR, f"{split}data")
        kaggle_crop_dir = os.path.join(DATA_DIR, f"{split}crop")
        
        if not os.path.exists(self.images_dir):
            if os.path.exists(kaggle_dir):
                self.images_dir = kaggle_dir
                self.masks_dir = kaggle_dir
            elif os.path.exists(kaggle_crop_dir):
                self.images_dir = kaggle_crop_dir
                self.masks_dir = kaggle_crop_dir
            elif os.path.exists(self.split_dir):
                self.images_dir = self.split_dir
                self.masks_dir = self.split_dir
                
        if not os.path.exists(self.images_dir):
            self.images = []
        else:
            self.images = [f for f in os.listdir(self.images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.bmp'))]

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.images_dir, img_name)
        
        # Try to find corresponding mask
        base_name = img_name.rsplit('.', 1)[0]
        mask_path = os.path.join(self.masks_dir, base_name + '.png')
        if not os.path.exists(mask_path):
            alt_mask = os.path.join(self.masks_dir, base_name + '_mask.png')
            if os.path.exists(alt_mask):
                mask_path = alt_mask

        # Load image
        img = cv2.imread(img_path)
        img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1)) # HWC to CHW

        # Load mask
        if os.path.exists(mask_path):
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        else:
            mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)
        mask = cv2.resize(mask, (IMAGE_SIZE, IMAGE_SIZE))
        mask = mask.astype(np.float32) / 255.0
        mask = np.expand_dims(mask, axis=0) # 1HW

        return torch.tensor(img), torch.tensor(mask)

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    model = UNet(in_channels=3, out_channels=1).to(device)
    
    # Class imbalance fix: Cracks are rare, so we heavily weight the positive class (cracks)
    # Typically cracks are ~2-5% of the image. A weight of 15-20 helps significantly.
    pos_weight = torch.tensor([15.0]).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    optimizer = optim.Adam(model.parameters(), lr=LR)

    train_dataset = CrackDataset('train')
    if len(train_dataset) == 0:
        print("No training data found. Make sure Phase 1 is fully executed.")
        return

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

    best_loss = float('inf')
    
    # We will simulate the training if it's too long or just run it. 
    # For a real pipeline, it runs EPOCHS times.
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0
        
        loop = tqdm(train_loader, leave=True)
        for i, (images, masks) in enumerate(loop):
            images, masks = images.to(device), masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            loop.set_description(f"Epoch [{epoch+1}/{EPOCHS}]")
            loop.set_postfix(loss=loss.item())
            
        avg_loss = epoch_loss / len(train_loader)
        print(f"Epoch [{epoch+1}/{EPOCHS}] completed. Average Loss: {avg_loss:.4f}")
        
        if avg_loss < best_loss:
            best_loss = avg_loss
            save_path = os.path.join(WEIGHTS_DIR, 'best_segmentation.pt')
            torch.save(model.state_dict(), save_path)
            print(f"Saved best model to {save_path}")

if __name__ == '__main__':
    train()
