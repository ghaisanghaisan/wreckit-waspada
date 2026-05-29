from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("apriandito/indobert-binary-sentiment-classifier")
model = AutoModelForSequenceClassification.from_pretrained("apriandito/indobert-binary-sentiment-classifier")
model.eval()

LABELS = {0: "Negatif", 1: "Positif"}

context = "harga sembako"
text = "harga beras naik terus bikin rakyat susah"

encoding = tokenizer(context, text, truncation=True, max_length=256, return_tensors="pt")
with torch.no_grad():
    probs = torch.softmax(model(**encoding).logits, dim=-1)[0]
    pred = torch.argmax(probs).item()

print(f"{LABELS[pred]} ({probs[pred]:.4f})")
# Output: Negatif (0.9987)

# 1. Initialize the NER pipeline with a fine-tuned BERT model
ner_pipeline = pipeline(
    "ner", 
    model="dslim/bert-base-NER", 
    aggregation_strategy="simple"
)

# 2. Initialize the Sentiment Analysis pipeline
sentiment_pipeline = pipeline(
    "sentiment-analysis", 
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

def analyze_entity_sentiment(text):
    print(f"Original Text: '{text}'\n")
    
    # Run NER to find entities
    entities = ner_pipeline(text)
    
    if not entities:
        print("No specific entities found. Running global sentiment:")
        print(sentiment_pipeline(text))
        return

    # Process sentiment for each discovered entity
    for entity in entities:
        word = entity['word']
        entity_group = entity['entity_group']
        
        # To get accurate sentiment for a specific entity, we look at the sentence 
        # but isolate the context. For simple applications, we pass the whole sentence,
        # but focus our output reporting on the entity.
        # (For advanced ABSA, you would slice the text around the entity's start/end indices)
        
        sentiment = sentiment_pipeline(text)[0]
        
        print(f"-> Entity Found: '{word}' ({entity_group})")
        print(f"   Context Sentiment: {sentiment['label']} (Score: {sentiment['score']:.2f})")
        print("-" * 40)

# Example text with mixed sentiments about different entities
text_input = "Google's new Pixel phone has an amazing camera, but Microsoft's support team was useless when I called them."
analyze_entity_sentiment(text_input)
