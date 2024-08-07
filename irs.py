import math
from sentence_transformers import SentenceTransformer
import torch

def bm25_plus(query, document, corpus, k1=1.2, b=0.75, delta=0.5):
    # Calculate the term frequency (TF)
    tf = {}
    for term in query:
        tf[term] = document.count(term)

    # Calculate the inverse document frequency (IDF)
    idf = {}
    for term in query:
        if(sum(1 for doc in corpus if term in doc[1].lower().split())) != 0:
            idf[term] = math.log((len(corpus) - sum(1 for doc in corpus if term in doc)) / sum(1 for doc in corpus if term in doc))
        else:
            idf[term] = 0
    # Calculate the BM25 score
    score = 0
    for term in query:
        score += (tf[term] * idf[term]) / (tf[term] + k1 * (1 - b + b * len(document) / sum(len(doc) for doc in corpus)))

    # Add the document length correction factor
    score += delta * len(document) / sum(len(doc) for doc in corpus)

    return score

def sentence_embd(query, vects):
    vects = torch.from_numpy(vects).float()
    model = SentenceTransformer("msmarco-roberta-base-v3")
    emb_q = model.encode([query])
    # Compute cosine similarities
    similarities = model.similarity(emb_q, vects)
    return similarities.tolist()[0]

# # Example usage
# query = ["example", "document"]
# document = ["This", "is", "an", "example", "document"]
# corpus = [["This", "is", "another", "document"], ["This", "is", "a", "test", "document"]]

# score = bm25_plus(query, document, corpus)

# print(score)