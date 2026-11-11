import csv
import sys
from pathlib import Path
import numpy as np


from PIL import Image
from sentence_transformers import SentenceTransformer

representative_paths = set()

with open(sys.argv[1], newline = "", encoding = "utf-8") as file:
    for row in csv.DictReader(file):
        representative_paths.add(row["representative_frame_path"])

image_paths = sorted(representative_paths)
images = []

for path in image_paths:
    with Image.open(path) as image:
        images.append(image.convert("RGB"))

model = SentenceTransformer("sentence-transformers/clip-ViT-B-32", device = "cpu")
embeddings = model.encode(images, normalize_embeddings= True)

output_path = Path(sys.argv[1]).with_name("image_embeddings.npz")
np.savez(
    output_path,
    image_paths = np.asarray(image_paths, dtype=str),
    embeddings=embeddings,
)
print("Saved:", output_path)
print("Embedding shape:", embeddings.shape)