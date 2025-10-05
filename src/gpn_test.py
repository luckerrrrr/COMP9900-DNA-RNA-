import gpn.model
from transformers import AutoModel, AutoModelForMaskedLM

model = AutoModel.from_pretrained("songlab/gpn-brassicales")
# or
model = AutoModelForMaskedLM.from_pretrained("songlab/gpn-brassicales")
