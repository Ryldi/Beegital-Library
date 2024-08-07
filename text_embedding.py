from transformers import DistilBertTokenizer, DistilBertModel
import torch
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Load pre-trained DistilBERT tokenizer and model
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertModel.from_pretrained('distilbert-base-uncased')

# extract embeddings
def get_embedding(text):
    # Tokenize text and ensure it's no longer than the maximum sequence length (512 tokens)
    tokens = tokenizer.encode(text[:512], add_special_tokens=True, return_tensors='pt')
    
    # Pad or truncate the tokens to ensure a fixed length of 512 tokens
    tokens = torch.cat([tokens, torch.zeros(1, 512 - tokens.shape[1], dtype=torch.long)], dim=1) if tokens.shape[1] < 512 else tokens[:, :512]
    
    with torch.no_grad():
        outputs = model(tokens)
        embeddings = outputs.last_hidden_state
    cls_embedding = embeddings[:, 0, :].numpy()
    
    return cls_embedding

def text_embed_string(data):
    # Process texts asynchronously and in parallel
    with ThreadPoolExecutor() as executor:
        # change generator type to list then into array
        embedding_text = np.array(list(executor.map(get_embedding, data)))
        
    # reshaping the array
    reshape_text = embedding_text.reshape(1, -1)

    # change nparray into string
    result_string = np.array2string(reshape_text, formatter={'float_kind':lambda x: "%.40f" % x})

    return result_string
    