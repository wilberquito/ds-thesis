"""
This module defines:
    - Melanoma dataset
    - A way of creating the train and test df
    - Transformations to be applied to the images of datasets
    - A function to split stratified in train and test sets
"""
import pandas as pd
from torch.utils.data import Dataset
import os
import numpy as np
import cv2
from sklearn.model_selection import train_test_split
import albumentations as A
from typing import Tuple
import torch


class MelanomaDataset(Dataset):
    """Definition of the dataset for the melanoma problem.
    By default takes the PIL image and transform to a tensor.
    """

    def __init__(self,
                 csv: pd.DataFrame,
                 mode: str,
                 transforms=None,
                 idx_to_class: dict = None):
        self.csv = csv.reset_index(drop=True)
        self.mode = mode
        self.transforms = transforms
        self.idx_to_class = idx_to_class
        self.classes = list(idx_to_class.keys())

    def __len__(self):
        return self.csv.shape[0]

    def __getitem__(self, index):

        # Get image path
        csv_sample = self.csv.iloc[index]

        # Read image from path, transforming to tree channels, rgb
        image_path = csv_sample['filepath']
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Transform the images using `albumentation`
        if self.transforms is not None:
            augmented = self.transforms(image=image)
            image = augmented['image'].astype(np.float32)
        else:
            image = image.astype(np.float32)

        # Channel first
        image = image.transpose(2, 0, 1)

        # If this is just for a test porpouse you can forget the label
        if self.mode == 'test':
            return torch.tensor(image).float()
        else:
            label = csv_sample['target']
            return torch.tensor(image).float(), label


def get_df(data_dir: str, data_folder: str):
    """
    Description
    -----------
    Generates the training and testing dataframe
    Joins the classes of the differents competitions into 8 final classes.
    Returns
    -------
        (train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        mapping_classes: Dict)
    """
    def img_path_builder(src: str, image_name: str, kind: str):
        return os.path.join(data_dir,
                            f'jpeg-{src}-{data_folder}x{data_folder}/{kind}',
                            f'{image_name}.jpg')

    def csv_path_builder(src: str, kind: str):
        return os.path.join(data_dir,
                            f'jpeg-{src}-{data_folder}x{data_folder}',
                            f'{kind}.csv')
    # 2020 data
    train_path = csv_path_builder('melanoma', 'train')
    df_train = pd.read_csv(train_path)

    # Drop samples without `tfrecord`
    df_train = df_train[df_train['tfrecord'] >= 0] \
        .reset_index(drop=True)

    # Generates new column with the path of each img
    df_train['filepath'] = df_train['image_name'] \
        .apply(lambda name: img_path_builder('melanoma', name, 'train'))

    # 2018, 2019 data (external data)
    ext_train_path = csv_path_builder('isic2019', 'train')
    ext_df_train = pd.read_csv(ext_train_path)

    # Drop samples without `tfrecord`
    ext_df_train = ext_df_train[ext_df_train['tfrecord'] >= 0] \
        .reset_index(drop=True)

    # Generates new column with the path of each img
    ext_df_train['filepath'] = ext_df_train['image_name'] \
        .apply(lambda name: img_path_builder('isic2019', name, 'train'))

    # Preprocess Target
    df_train['diagnosis'] = df_train['diagnosis'] \
        .apply(lambda x: x.replace('seborrheic keratosis', 'BKL'))
    df_train['diagnosis'] = df_train['diagnosis'] \
        .apply(lambda x: x.replace('lichenoid keratosis', 'BKL'))
    df_train['diagnosis'] = df_train['diagnosis'] \
        .apply(lambda x: x.replace('solar lentigo', 'BKL'))
    df_train['diagnosis'] = df_train['diagnosis'] \
        .apply(lambda x: x.replace('lentigo NOS', 'BKL'))
    df_train['diagnosis'] = df_train['diagnosis'] \
        .apply(lambda x: x.replace('cafe-au-lait macule', 'unknown'))
    df_train['diagnosis'] = df_train['diagnosis'] \
        .apply(lambda x: x.replace('atypical melanocytic proliferation', 'unknown'))

    ext_df_train['diagnosis'] = ext_df_train['diagnosis'] \
        .apply(lambda x: x.replace('NV', 'nevus'))
    ext_df_train['diagnosis'] = ext_df_train['diagnosis'] \
        .apply(lambda x: x.replace('MEL', 'melanoma'))

    # Concat train data
    df_train = pd.concat([df_train, ext_df_train]) \
        .reset_index(drop=True)

    # Test data
    df_test = pd.read_csv(csv_path_builder('melanoma', 'test'))
    df_test['filepath'] = df_test['image_name'] \
        .apply(lambda name: img_path_builder('melanoma', name, 'test'))

    # Mapping
    uniques = enumerate(sorted(df_train['diagnosis'].unique()))
    diagnosis2idx = {d: idx for idx, d in uniques}
    df_train['target'] = df_train['diagnosis'].map(diagnosis2idx)

    return df_train, df_test, diagnosis2idx


def get_transforms(image_size: int,
                   mean: Tuple[int, int, int] = None,
                   std: Tuple[int, int, int] = None):
    """
    Returns a pair of transformers.
    The first transformer applies image augmentation of different kinds and resize the image.
    The second transformer, is thought to be used in test data, resizes and normalize the image.
    """

    # Standard values for imagenet models
    if mean is None:
        mean = (0.485, 0.456, 0.406)
    if std is None:
        std = (0.229, 0.224, 0.225)

    transforms_train = A.Compose([
        A.Transpose(p=0.5),
        A.VerticalFlip(p=0.5),
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(contrast_limit=0.2, p=0.75),
        A.OneOf([
            A.MotionBlur(blur_limit=5),
            A.MedianBlur(blur_limit=5),
            A.GaussianBlur(blur_limit=5),
            A.GaussNoise(var_limit=(5.0, 30.0)),
        ], p=0.7),
        A.OneOf([
            A.OpticalDistortion(distort_limit=1.0),
            A.GridDistortion(num_steps=5, distort_limit=1.),
            A.ElasticTransform(alpha=3),
        ], p=0.7),
        A.CLAHE(clip_limit=4.0, p=0.7),
        A.HueSaturationValue(hue_shift_limit=10,
                             sat_shift_limit=20,
                             val_shift_limit=10,
                             p=0.5),
        A.ShiftScaleRotate(shift_limit=0.1,
                           scale_limit=0.1,
                           rotate_limit=15,
                           border_mode=0,
                           p=0.85),
        A.Resize(image_size, image_size),
        A.CoarseDropout(max_holes=1,
                        max_height=int(image_size * 0.375),
                        max_width=int(image_size * 0.375),
                        p=0.7),
        A.Normalize(mean=mean, std=std)
    ])

    transforms_val = A.Compose([
        A.Resize(image_size, image_size),
        A.Normalize(mean=mean, std=std)
    ])

    return transforms_train, transforms_val


def train_validate_split(df: pd.DataFrame,
                         random_state: int = 42,
                         validate_size: int = 0.25):
    """Split dataframe into random train and validate dataframe,
    it uses stratify thecnique because of the unbalanced dataset"""

    X_train, X_val = train_test_split(df,
                                      random_state=random_state,
                                      train_size=(1-validate_size),
                                      stratify=df['target'])
    X_train = pd.DataFrame(X_train)
    X_train.columns = df.columns
    X_val = pd.DataFrame(X_val)
    X_val.columns = df.columns

    return X_train, X_val
