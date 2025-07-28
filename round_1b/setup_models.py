#!/usr/bin/env python3
"""
Model Setup Script for Round 1B
Downloads and organizes models for offline use
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def download_spacy_model():
    """Download spaCy model to local directory"""
    print("📥 Downloading spaCy model...")
    try:
        # Download spaCy model
        subprocess.run([
            sys.executable, "-m", "spacy", "download", "en_core_web_sm"
        ], check=True)
        
        # Get the model path
        import spacy
        model_path = spacy.util.get_package_path('en_core_web_sm')
        
        # Copy to local models directory
        local_model_dir = Path("models/spacy/en_core_web_sm")
        local_model_dir.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(model_path):
            shutil.copytree(model_path, local_model_dir, dirs_exist_ok=True)
            print(f"✅ spaCy model copied to: {local_model_dir}")
        else:
            print("❌ spaCy model not found")
            
    except Exception as e:
        print(f"❌ Error downloading spaCy model: {e}")

def download_sentence_transformer():
    """Download sentence transformer model"""
    print("📥 Downloading sentence transformer model...")
    try:
        from sentence_transformers import SentenceTransformer
        
        # Create models directory
        models_dir = Path("models/sentence_transformers")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download and cache the model
        model = SentenceTransformer('intfloat/e5-small')
        
        # Save model locally
        model_path = models_dir / "intfloat_e5_small"
        model.save(str(model_path))
        
        print(f"✅ Sentence transformer model saved to: {model_path}")
        
    except Exception as e:
        print(f"❌ Error downloading sentence transformer: {e}")

def create_model_config():
    """Create model configuration file"""
    config = {
        "spacy_model": "models/spacy/en_core_web_sm",
        "sentence_transformer": "models/sentence_transformers/intfloat_e5_small",
        "models_downloaded": True,
        "offline_ready": True
    }
    
    import json
    with open("models/model_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Model configuration created")

def main():
    """Main setup function"""
    print("🚀 Setting up models for offline use...")
    
    # Create models directory
    Path("models").mkdir(exist_ok=True)
    
    # Download models
    download_spacy_model()
    download_sentence_transformer()
    
    # Create configuration
    create_model_config()
    
    print("\n✅ Model setup complete!")
    print("📁 Models are now available in the 'models/' directory")
    print("🔧 Update your code to use local model paths for offline execution")

if __name__ == "__main__":
    main() 