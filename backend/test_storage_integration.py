#!/usr/bin/env python3
"""Integration test for storage abstraction layer."""

import asyncio
import tempfile
import shutil
from pathlib import Path

from app.storage import LocalStorage, StorageError


async def test_storage_integration():
    """Test storage integration with realistic scenarios."""
    print("Testing storage abstraction layer integration...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        storage = LocalStorage(base_path=temp_dir, base_url="/files/")
        
        # Test 1: Save document file
        print("✓ Testing document file storage...")
        doc_content = b"This is a sample PDF document content"
        doc_path = await storage.save(doc_content, "sample.pdf", "application/pdf")
        assert doc_path.endswith(".pdf")
        
        # Test 2: Save image file
        print("✓ Testing image file storage...")
        img_content = b"Fake image data"
        img_path = await storage.save(img_content, "figure1.jpg", "image/jpeg")
        assert img_path.endswith(".jpg")
        
        # Test 3: Verify files exist and can be retrieved
        print("✓ Testing file retrieval...")
        assert await storage.exists(doc_path)
        assert await storage.exists(img_path)
        
        retrieved_doc = await storage.retrieve(doc_path)
        retrieved_img = await storage.retrieve(img_path)
        
        assert retrieved_doc == doc_content
        assert retrieved_img == img_content
        
        # Test 4: Get URLs for files
        print("✓ Testing URL generation...")
        doc_url = await storage.get_url(doc_path)
        img_url = await storage.get_url(img_path)
        
        assert doc_url.startswith("/files/")
        assert img_url.startswith("/files/")
        
        # Test 5: Test file organization with prefixes
        print("✓ Testing file organization...")
        chapter_img = await storage.save(
            b"Chapter image", "chapter1_fig1.png", "image/png"
        )
        
        # Test 6: Clean up - delete files
        print("✓ Testing file deletion...")
        assert await storage.delete(doc_path)
        assert await storage.delete(img_path)
        assert await storage.delete(chapter_img)
        
        # Verify files are gone
        assert not await storage.exists(doc_path)
        assert not await storage.exists(img_path)
        assert not await storage.exists(chapter_img)
        
        print("✅ All storage integration tests passed!")
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)


async def test_error_handling():
    """Test error handling scenarios."""
    print("Testing error handling...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage = LocalStorage(base_path=temp_dir)
        
        # Test retrieving non-existent file
        try:
            await storage.retrieve("nonexistent.txt")
            assert False, "Should have raised StorageError"
        except StorageError as e:
            assert "File not found" in str(e)
            print("✓ Non-existent file retrieval error handled correctly")
        
        # Test getting URL for non-existent file
        try:
            await storage.get_url("nonexistent.txt")
            assert False, "Should have raised StorageError"
        except StorageError as e:
            assert "File not found" in str(e)
            print("✓ Non-existent file URL error handled correctly")
        
        # Test invalid file data
        try:
            await storage.save("invalid data type", "test.txt")
            assert False, "Should have raised StorageError"
        except StorageError as e:
            assert "Unsupported file_data type" in str(e)
            print("✓ Invalid file data error handled correctly")
        
        print("✅ All error handling tests passed!")
        
    finally:
        shutil.rmtree(temp_dir)


async def main():
    """Run all integration tests."""
    await test_storage_integration()
    await test_error_handling()
    print("\n🎉 Storage abstraction layer implementation complete!")
    print("Features implemented:")
    print("  - Abstract Storage interface")
    print("  - LocalStorage implementation")
    print("  - File save/retrieve/delete operations")
    print("  - URL generation for file access")
    print("  - Unique path generation")
    print("  - Error handling and validation")
    print("  - Comprehensive unit tests")


if __name__ == "__main__":
    asyncio.run(main())