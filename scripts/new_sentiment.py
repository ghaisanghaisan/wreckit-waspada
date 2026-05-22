import warnings
from transformers import pipeline

# Suppress warnings for cleaner console output
warnings.filterwarnings("ignore")

def main():
    print("Loading models from Hugging Face (this may take a minute on first run)...")
    
    # 1. Load the NLP Pipelines
    # NER Pipeline: Extracts standard Indonesian entities (PER, ORG, LOC)
    # aggregation_strategy="simple" merges sub-tokens (e.g., "Sri" and "Mulyani" into one entity)
    ner_pipe = pipeline("ner", model="cahya/bert-base-indonesian-NER", aggregation_strategy="simple")
    
    # Sentiment Pipeline: Classifies text into Positive, Negative, or Neutral
    sentiment_pipe = pipeline("text-classification", model="Aardiiiiy/indobertweet-base-Indonesian-sentiment-analysis")
    
    # 2. Sample News Article
    # Notice the mixed sentiment: Negative towards Kementerian Pertanian, Positive towards Kementerian Kesehatan.
    news_text = (
        "Menteri Keuangan Sri Mulyani mengumumkan pemotongan anggaran "
        "karena kinerja Kementerian Pertanian yang dinilai sangat mengecewakan. "
        "Namun, Sri Mulyani memberikan apresiasi tinggi kepada Kementerian Kesehatan "
        "atas keberhasilan program vaksinasi."
    )
    
    print("\n--- SAMPLE NEWS ARTICLE ---")
    print(news_text)
    print("---------------------------\n")

    # ==========================================
    # LAYER 1: Document-Level Sentiment
    # ==========================================
    print("[LAYER 1] Document-Level Sentiment:")
    doc_sentiment = sentiment_pipe(news_text)[0]
    print(f"Overall Sentiment: {doc_sentiment['label']} (Score: {doc_sentiment['score']:.4f})\n")

    # ==========================================
    # NER: Extracting Entities
    # ==========================================
    print("[NER] Extracted Entities:")
    entities = ner_pipe(news_text)
    
    extracted_entities = []
    for ent in entities:
        print(f" - {ent['word']} (Type: {ent['entity_group']}, Confidence: {ent['score']:.4f})")
        extracted_entities.append(ent['word'])
        
    print("\n[LAYER 2] Entity-Level Sentiment (Context Window Heuristic):")
    
    # ==========================================
    # LAYER 2: Entity-Level Sentiment (ABSA mock)
    # ==========================================
    # For a pure PoC, we split the document into sentences. 
    # We evaluate the sentiment of the specific sentence where the entity is mentioned.
    sentences = [s.strip() + "." for s in news_text.split(".") if s.strip()]
    
    # Use a set to avoid processing the same entity twice
    for entity in set(extracted_entities):
        # Find which sentence(s) contain the entity
        for sentence in sentences:
            if entity in sentence:
                # Run the sentiment model *only* on the isolated context
                ent_sentiment = sentiment_pipe(sentence)[0]
                print(f" Entity : {entity}")
                print(f" Context: '{sentence}'")
                print(f" Verdict: {ent_sentiment['label']} (Score: {ent_sentiment['score']:.4f})\n")

if __name__ == "__main__":
    main()
