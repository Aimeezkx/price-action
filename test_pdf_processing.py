#!/usr/bin/env python3
"""
Comprehensive PDF Processing Test Script
Tests the document learning app with PDF files from the resource folder
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Add backend to path
sys.path.append('backend')

BASE_URL = "http://localhost:8000"
RESOURCE_DIR = "resource"

def test_server_health():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Server health check: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running")
        return False

def get_pdf_files():
    """Get all PDF files from resource directory"""
    pdf_files = []
    if os.path.exists(RESOURCE_DIR):
        for file in os.listdir(RESOURCE_DIR):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(RESOURCE_DIR, file))
    return pdf_files

def test_pdf_upload(pdf_path):
    """Test uploading a PDF file"""
    print(f"\n--- Testing PDF Upload: {os.path.basename(pdf_path)} ---")
    
    # Check file size first
    file_size = os.path.getsize(pdf_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"File size: {file_size_mb:.1f}MB")
    
    # Skip very large files
    if file_size_mb > 500:
        print(f"✗ Skipping large file (>{500}MB)")
        return None
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            # Increase timeout for large files
            timeout = max(30, int(file_size_mb / 10))  # 1 second per 10MB, min 30s
            response = requests.post(f"{BASE_URL}/api/documents/upload", files=files, timeout=timeout)
            
        print(f"Upload status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Upload successful - Document ID: {result.get('id')}")
            print(f"  Status: {result.get('status')}")
            print(f"  Pages: {result.get('page_count')}")
            return result.get('id')
        else:
            print(f"✗ Upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Upload error: {str(e)}")
        return None

def test_document_processing(doc_id):
    """Test document processing pipeline"""
    print(f"\n--- Testing Document Processing: {doc_id} ---")
    
    # Test document details
    try:
        response = requests.get(f"{BASE_URL}/api/documents/{doc_id}")
        if response.status_code == 200:
            doc = response.json()
            print(f"✓ Document retrieved: {doc.get('title', 'No title')}")
            print(f"  Status: {doc.get('status', 'Unknown')}")
            print(f"  Pages: {doc.get('page_count', 'Unknown')}")
        else:
            print(f"✗ Failed to get document: {response.status_code}")
    except Exception as e:
        print(f"✗ Document retrieval error: {str(e)}")

def test_chapter_extraction(doc_id):
    """Test chapter extraction"""
    print(f"\n--- Testing Chapter Extraction: {doc_id} ---")
    
    try:
        response = requests.get(f"{BASE_URL}/api/documents/{doc_id}/chapters")
        if response.status_code == 200:
            chapters = response.json()
            print(f"✓ Chapters extracted: {len(chapters)} chapters")
            for i, chapter in enumerate(chapters[:3]):  # Show first 3
                print(f"  Chapter {i+1}: {chapter.get('title', 'No title')}")
        else:
            print(f"✗ Chapter extraction failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Chapter extraction error: {str(e)}")

def test_knowledge_extraction(doc_id):
    """Test knowledge point extraction"""
    print(f"\n--- Testing Knowledge Extraction: {doc_id} ---")
    
    try:
        response = requests.get(f"{BASE_URL}/api/documents/{doc_id}/knowledge-points")
        if response.status_code == 200:
            knowledge_points = response.json()
            print(f"✓ Knowledge points extracted: {len(knowledge_points)} points")
            for i, kp in enumerate(knowledge_points[:3]):  # Show first 3
                print(f"  KP {i+1}: {kp.get('title', 'No title')}")
        else:
            print(f"✗ Knowledge extraction failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Knowledge extraction error: {str(e)}")

def test_card_generation(doc_id):
    """Test flashcard generation"""
    print(f"\n--- Testing Card Generation: {doc_id} ---")
    
    try:
        response = requests.post(f"{BASE_URL}/api/documents/{doc_id}/generate-cards")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Cards generated: {result.get('count', 0)} cards")
        else:
            print(f"✗ Card generation failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Card generation error: {str(e)}")

def test_search_functionality(doc_id):
    """Test search functionality"""
    print(f"\n--- Testing Search Functionality ---")
    
    search_terms = ["trading", "trend", "price", "market"]
    
    for term in search_terms:
        try:
            response = requests.get(f"{BASE_URL}/api/search", params={"q": term})
            if response.status_code == 200:
                results = response.json()
                print(f"✓ Search '{term}': {len(results)} results")
            else:
                print(f"✗ Search '{term}' failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Search error for '{term}': {str(e)}")

def main():
    """Main test function"""
    print("=== PDF Processing Test Suite ===")
    
    # Check server health
    if not test_server_health():
        print("Server is not running. Please start the backend server first.")
        return
    
    # Get PDF files
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("No PDF files found in resource directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"  - {os.path.basename(pdf)}")
    
    # Test each PDF file
    document_ids = []
    for pdf_path in pdf_files:
        doc_id = test_pdf_upload(pdf_path)
        if doc_id:
            document_ids.append(doc_id)
            
            # Wait a bit for processing
            time.sleep(2)
            
            # Test processing pipeline
            test_document_processing(doc_id)
            test_chapter_extraction(doc_id)
            test_knowledge_extraction(doc_id)
            test_card_generation(doc_id)
    
    # Test search functionality
    if document_ids:
        test_search_functionality(document_ids[0])
    
    print("\n=== Test Summary ===")
    print(f"Processed {len(document_ids)} out of {len(pdf_files)} PDF files")
    
    if len(document_ids) < len(pdf_files):
        print("Some files failed to upload. Check the errors above.")
    else:
        print("All PDF files processed successfully!")

if __name__ == "__main__":
    main()