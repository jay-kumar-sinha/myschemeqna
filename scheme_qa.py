import torch
from sentence_transformers import SentenceTransformer
import faiss
import json
import pandas as pd
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import os
from tqdm import tqdm
from typing import List, Dict, Any, Tuple

class SchemeQASystem:
    def __init__(self, 
                 chunks_file="scheme_chunks.json",
                 processed_data_file="processed_schemes.json",
                 use_gpu=True):
        """Initialize the QA system with the processed data"""
        # Device configuration
        self.device = "cuda" if torch.cuda.is_available() and use_gpu else "cpu"
        print(f"Using device: {self.device}")
        
        # Load the processed data
        with open(chunks_file, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        with open(processed_data_file, 'r', encoding='utf-8') as f:
            self.schemes = json.load(f)
        
        # Create scheme lookup by ID
        self.scheme_lookup = {scheme['id']: scheme for scheme in self.schemes}
        
        # Initialize embedding model (small but effective)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=self.device)
        
        # Initialize LLM for generation
        print("Loading language model...")
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Small but capable model
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        
        # Build the vector database
        print("Building vector database...")
        self._build_vector_db()
    
    def _build_vector_db(self):
        """Build a FAISS vector database from the chunks"""
        # Generate embeddings for all chunks
        texts = [chunk['text'] for chunk in self.chunks]
        
        # Process in batches to avoid memory issues
        batch_size = 32
        all_embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size)):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.embedding_model.encode(batch_texts, convert_to_tensor=True)
            batch_embeddings = batch_embeddings.cpu().numpy()
            all_embeddings.append(batch_embeddings)
        
        embeddings = np.vstack(all_embeddings)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        embedding_dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
        self.index.add(embeddings)
        
        print(f"Vector database built with {len(self.chunks)} chunks")
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most relevant chunks for a query"""
        # Encode the query
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
        query_embedding = query_embedding.cpu().numpy().reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search for similar chunks
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Get the relevant chunks
        relevant_chunks = [
            {
                **self.chunks[idx],
                "score": float(scores[0][i])
            }
            for i, idx in enumerate(indices[0])
        ]
        
        return relevant_chunks
    
    def generate_answer(self, query: str, top_k: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate an answer to the query using the retrieved chunks"""
        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k)
        
        # Create context from relevant chunks
        context = "\n\n".join([
            f"[Scheme: {chunk['scheme_name']}]\n" +
            f"Information: {chunk['text']}"
            for chunk in relevant_chunks
        ])
        
        # Construct prompt for the LLM
        prompt = f"""You are a helpful assistant that provides information about Indian government schemes.
Based on the following context, please answer the question accurately and concisely.
If you don't find relevant information in the context, just say you don't have enough information.

Context:
{context}

Question: {query}

Answer:"""
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        # Return the answer and the relevant chunks for transparency
        return response.strip(), relevant_chunks
    
    def get_scheme_suggestions(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Suggest schemes based on the query"""
        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k=10)
        
        # Count schemes that appear in the results
        scheme_counts = {}
        for chunk in relevant_chunks:
            scheme_id = chunk['scheme_id']
            if scheme_id in scheme_counts:
                scheme_counts[scheme_id] += chunk['score']
            else:
                scheme_counts[scheme_id] = chunk['score']
        
        # Get the top schemes
        top_schemes = sorted(scheme_counts.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Get the full scheme details
        suggestions = []
        for scheme_id, score in top_schemes:
            scheme = self.scheme_lookup.get(scheme_id, {})
            if scheme:
                suggestions.append({
                    "id": scheme_id,
                    "name": scheme.get('name', ''),
                    "description": scheme.get('description', ''),
                    "ministries": scheme.get('ministries', ''),
                    "beneficiaries": scheme.get('beneficiaries', ''),
                    "score": float(score)
                })
        
        return suggestions

    def answer_query(self, query: str) -> Dict[str, Any]:
        """Comprehensive answer to a query with relevant schemes and information"""
        answer, relevant_chunks = self.generate_answer(query)
        suggestions = self.get_scheme_suggestions(query)
        
        return {
            "query": query,
            "answer": answer,
            "relevant_schemes": suggestions,
            "chunks_used": relevant_chunks
        }

# Example usage
if __name__ == "__main__":
    qa_system = SchemeQASystem()
    
    # Test queries
    test_queries = [
        "What schemes are available for farmers in Maharashtra?",
        "Are there any schemes for women entrepreneurs?",
        "What schemes provide financial assistance for education?",
        "How can senior citizens benefit from government schemes?",
        "What schemes help with affordable housing?"
    ]
    
    # Test the system
    print("\nTesting the QA system with sample queries:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = qa_system.answer_query(query)
        print(f"Answer: {result['answer']}")
        print("\nTop Suggested Schemes:")
        for scheme in result['relevant_schemes'][:2]:
            print(f"- {scheme['name']}: {scheme['description'][:100]}...")
        print("-" * 80)