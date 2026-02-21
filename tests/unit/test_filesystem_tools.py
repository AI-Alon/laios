"""
Tests for filesystem tools
"""

import pytest
import tempfile
from pathlib import Path

from laios.tools.builtin.filesystem import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    GetFileInfoTool,
)


class TestReadFileTool:
    """Tests for ReadFileTool"""
    
    def test_read_existing_file(self, tmp_path):
        """Test reading an existing file"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, LAIOS!")
        
        # Execute tool
        tool = ReadFileTool()
        result = tool.execute(path=str(test_file))
        
        assert result.success
        assert result.data == "Hello, LAIOS!"
        assert result.metadata["size_bytes"] > 0
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist"""
        tool = ReadFileTool()
        result = tool.execute(path="/nonexistent/file.txt")
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_read_directory_fails(self, tmp_path):
        """Test that reading a directory fails"""
        tool = ReadFileTool()
        result = tool.execute(path=str(tmp_path))
        
        assert not result.success
        assert "not a file" in result.error.lower()


class TestWriteFileTool:
    """Tests for WriteFileTool"""
    
    def test_write_new_file(self, tmp_path):
        """Test writing a new file"""
        test_file = tmp_path / "new_file.txt"
        
        tool = WriteFileTool()
        result = tool.execute(
            path=str(test_file),
            content="Test content"
        )
        
        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "Test content"
    
    def test_write_creates_directories(self, tmp_path):
        """Test that parent directories are created"""
        test_file = tmp_path / "subdir" / "deep" / "file.txt"
        
        tool = WriteFileTool()
        result = tool.execute(
            path=str(test_file),
            content="Deep file",
            create_dirs=True
        )
        
        assert result.success
        assert test_file.exists()
    
    def test_overwrite_existing_file(self, tmp_path):
        """Test overwriting an existing file"""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Original")
        
        tool = WriteFileTool()
        result = tool.execute(
            path=str(test_file),
            content="Updated"
        )
        
        assert result.success
        assert test_file.read_text() == "Updated"


class TestListDirectoryTool:
    """Tests for ListDirectoryTool"""
    
    def test_list_directory(self, tmp_path):
        """Test listing directory contents"""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        
        tool = ListDirectoryTool()
        result = tool.execute(path=str(tmp_path))
        
        assert result.success
        assert isinstance(result.data, list)
        assert len(result.data) >= 3
        
        names = [item["name"] for item in result.data]
        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names
    
    def test_list_with_pattern(self, tmp_path):
        """Test listing with glob pattern"""
        (tmp_path / "test.py").write_text("python")
        (tmp_path / "test.txt").write_text("text")
        (tmp_path / "readme.md").write_text("markdown")
        
        tool = ListDirectoryTool()
        result = tool.execute(path=str(tmp_path), pattern="*.py")
        
        assert result.success
        assert len(result.data) == 1
        assert result.data[0]["name"] == "test.py"
    
    def test_list_hidden_files(self, tmp_path):
        """Test including/excluding hidden files"""
        (tmp_path / "visible.txt").write_text("visible")
        (tmp_path / ".hidden").write_text("hidden")
        
        tool = ListDirectoryTool()
        
        # Without hidden files
        result1 = tool.execute(path=str(tmp_path), include_hidden=False)
        names1 = [item["name"] for item in result1.data]
        assert ".hidden" not in names1
        
        # With hidden files
        result2 = tool.execute(path=str(tmp_path), include_hidden=True)
        names2 = [item["name"] for item in result2.data]
        assert ".hidden" in names2


class TestGetFileInfoTool:
    """Tests for GetFileInfoTool"""
    
    def test_get_file_info(self, tmp_path):
        """Test getting file metadata"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")
        
        tool = GetFileInfoTool()
        result = tool.execute(path=str(test_file))
        
        assert result.success
        assert result.data["name"] == "test.txt"
        assert result.data["type"] == "file"
        assert result.data["size_bytes"] > 0
        assert "created" in result.data
        assert "modified" in result.data
    
    def test_get_directory_info(self, tmp_path):
        """Test getting directory metadata"""
        tool = GetFileInfoTool()
        result = tool.execute(path=str(tmp_path))
        
        assert result.success
        assert result.data["type"] == "directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
