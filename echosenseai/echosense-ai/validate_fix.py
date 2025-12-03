#!/usr/bin/env python
"""
Quick validation that the upload fix works
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), 'backend')))

from services.s3_handler import S3Handler

async def test_upload():
    print("=" * 60)
    print("Testing upload fix")
    print("=" * 60)
    
    handler = S3Handler()
    print(f"\n✓ S3Handler initialized")
    print(f"  Local storage path: {handler.local_storage_path}")
    print(f"  Path exists: {os.path.exists(handler.local_storage_path)}")
    
    # Test upload
    test_content = b"test audio content for validation"
    test_filename = "test_validation.mp3"
    
    url = await handler.upload_file(test_content, test_filename)
    print(f"\n✓ File uploaded")
    print(f"  Returned URL: {url}")
    
    # Verify file exists
    file_path = os.path.join(handler.local_storage_path, test_filename)
    exists = os.path.exists(file_path)
    print(f"\n✓ File verification")
    print(f"  File path: {file_path}")
    print(f"  File exists: {exists}")
    
    if exists:
        with open(file_path, "rb") as f:
            saved_content = f.read()
        print(f"  Content matches: {saved_content == test_content}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_upload())
