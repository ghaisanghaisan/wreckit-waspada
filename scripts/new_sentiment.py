from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("apriandito/indobert-binary-sentiment-classifier")
model = AutoModelForSequenceClassification.from_pretrained("apriandito/indobert-binary-sentiment-classifier")
model.to(device)
model.eval()

LABELS = {0: "Negatif", 1: "Positif"}

organizational_contexts = [
    "kualitas layanan",
    "layanan pelanggan",
    "harga",
    "aplikasi dan sistem"
]
text = "Gila ya ini bank aplikasinya sering banget error pas mau transfer, untung cs nya gercep dan ramah banget pas dibantu."

text_pairs = [text] * len(organizational_contexts)

encodings = tokenizer(
    organizational_contexts,  # List of contexts
    text_pairs,               # List of identical texts
    truncation=True, 
    padding=True,             # Ensures uniform matrix shapes for the batch
    max_length=256, 
    return_tensors="pt"
).to(device)

# 4. RUN SINGLE FORWARD PASS
with torch.no_grad():
    outputs = model(**encodings)
    # Compute softmax across the entire batch at once
    probs_batch = torch.softmax(outputs.logits, dim=-1)
    preds_batch = torch.argmax(probs_batch, dim=-1).tolist()

# 5. Print results instantly from memory
print(f"Review: '{text}'\n")
print("--- Optimized Batch Breakthrough Analysis ---")

end = 0
for i, context in enumerate(organizational_contexts):
    pred = preds_batch[i]
    prob = probs_batch[i][pred].item()
    if pred == "Positif":
        end +=1 

    print(f"Context: [{context:20}] -> Sentiment: {LABELS[pred]} ({prob:.4f})")

end /= len(organizational_contexts)

if end > 0.5:
    print("POSITIF")
else:
    print("NEGATIF")

