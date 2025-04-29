import pandas as pd
import json
import re
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

class SchemeDataProcessor:
    def __init__(self, input_file="myscheme_data.json"):
        self.stop_words = set(stopwords.words('english'))
        
        # Load the scraped data
        if input_file.endswith('.json'):
            with open(input_file, 'r', encoding='utf-8') as f:
                self.schemes = json.load(f)
        else:
            self.schemes = pd.read_csv(input_file).to_dict('records')
            
        self.processed_data = []
        self.chunks = []
    
    def clean_text(self, text):
        """Clean text by removing special characters and extra whitespace"""
        if not text or not isinstance(text, str):
            return ""
            
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_key_info(self):
        """Extract and format key information from each scheme"""
        for scheme in self.schemes:
            # Clean and format the fields
            name = self.clean_text(scheme.get('name', ''))
            description = self.clean_text(scheme.get('description', ''))
            ministries = ", ".join([self.clean_text(m) for m in scheme.get('ministries', [])])
            beneficiaries = ", ".join([self.clean_text(b) for b in scheme.get('target_beneficiaries', [])])
            eligibility = self.clean_text(scheme.get('eligibility_criteria', ''))
            benefits = self.clean_text(scheme.get('benefits', ''))
            application = self.clean_text(scheme.get('application_process', ''))
            tags = ", ".join([self.clean_text(t) for t in scheme.get('tags', [])])
            
            # Create structured document
            processed_scheme = {
                "id": scheme.get('id', ''),
                "name": name,
                "description": description,
                "ministries": ministries,
                "beneficiaries": beneficiaries,
                "eligibility": eligibility,
                "benefits": benefits,
                "application": application,
                "tags": tags,
                # Create a consolidated text for embedding
                "full_text": f"Scheme Name: {name}\n\nDescription: {description}\n\n"
                            f"Ministries/Departments: {ministries}\n\n"
                            f"Target Beneficiaries: {beneficiaries}\n\n"
                            f"Eligibility Criteria: {eligibility}\n\n"
                            f"Benefits: {benefits}\n\n"
                            f"Application Process: {application}\n\n"
                            f"Tags: {tags}"
            }
            
            self.processed_data.append(processed_scheme)
    
    def create_chunks(self, chunk_size=512, overlap=100):
        """Create overlapping chunks of the data for CRAG approach"""
        for scheme in self.processed_data:
            # Tokenize the full text into sentences
            sentences = sent_tokenize(scheme['full_text'])
            
            # Initialize chunks
            current_chunk = ""
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence.split())
                
                # If adding this sentence would exceed the chunk size, create a new chunk
                if current_length + sentence_length > chunk_size and current_length > 0:
                    # Add the chunk with metadata
                    self.chunks.append({
                        "scheme_id": scheme['id'],
                        "scheme_name": scheme['name'],
                        "text": current_chunk,
                        "ministries": scheme['ministries'],
                        "beneficiaries": scheme['beneficiaries'],
                        "tags": scheme['tags']
                    })
                    
                    # Start a new chunk with overlap
                    overlap_text = " ".join(current_chunk.split()[-overlap:]) if overlap > 0 else ""
                    current_chunk = overlap_text + " " + sentence
                    current_length = len(current_chunk.split())
                else:
                    # Add sentence to current chunk
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_length += sentence_length
            
            # Add the last chunk if there's anything left
            if current_chunk:
                self.chunks.append({
                    "scheme_id": scheme['id'],
                    "scheme_name": scheme['name'],
                    "text": current_chunk,
                    "ministries": scheme['ministries'],
                    "beneficiaries": scheme['beneficiaries'],
                    "tags": scheme['tags']
                })
    
    def extract_keywords(self, n_keywords=10):
        """Extract keywords from each scheme using TF-IDF"""
        corpus = [scheme['full_text'] for scheme in self.processed_data]
        vectorizer = TfidfVectorizer(max_features=500, stop_words=list(self.stop_words))
        tfidf_matrix = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
        
        # Extract top keywords for each scheme
        for i, scheme in enumerate(self.processed_data):
            # Get the TF-IDF scores for this document
            tfidf_scores = tfidf_matrix[i].toarray()[0]
            # Get the indices of the top n scores
            top_indices = tfidf_scores.argsort()[-n_keywords:][::-1]
            # Get the corresponding keywords
            top_keywords = [feature_names[idx] for idx in top_indices]
            # Add keywords to the scheme
            scheme['keywords'] = top_keywords
    
    def process(self):
        """Run the full processing pipeline"""
        print("Extracting and cleaning scheme information...")
        self.extract_key_info()
        
        print("Extracting keywords...")
        self.extract_keywords()
        
        print("Creating overlapping chunks for CRAG...")
        self.create_chunks()
        
        print(f"Processing complete. Generated {len(self.processed_data)} processed schemes and {len(self.chunks)} chunks.")
        return self.processed_data, self.chunks
    
    def save_processed_data(self, filename="processed_schemes.json"):
        """Save the processed schemes to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.processed_data, f, ensure_ascii=False, indent=4)
        print(f"Processed data saved to {filename}")
    
    def save_chunks(self, filename="scheme_chunks.json"):
        """Save the chunks to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)
        print(f"Chunks saved to {filename}")

if __name__ == "__main__":
    processor = SchemeDataProcessor()
    processed_data, chunks = processor.process()
    processor.save_processed_data()
    processor.save_chunks()