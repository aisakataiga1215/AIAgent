import pytest
from pathlib import Path
from src.rag.chunker import chunk_python_file, chunk_text_file, chunk_file, Chunk


def test_chunk_python_file(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("""
import os

def hello():
    '''Say hello.'''
    print("hello world")

class Greeter:
    def greet(self, name):
        return f"Hello, {name}"
""")
    chunks = chunk_python_file(f)
    assert len(chunks) >= 2
    names = {c.name for c in chunks}
    assert "hello" in names
    assert "Greeter" in names


def test_chunk_text_file(tmp_path):
    f = tmp_path / "readme.md"
    long_text = "\n".join(f"line {i}" for i in range(3000))
    f.write_text(long_text)
    chunks = chunk_text_file(f, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) >= 3


def test_chunk_text_file_small(tmp_path):
    f = tmp_path / "small.md"
    f.write_text("short file")
    chunks = chunk_text_file(f)
    assert len(chunks) == 1
    assert chunks[0].content == "short file"


def test_chunk_file_auto_detect_python(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("def foo():\n    return 1")
    chunks = chunk_file(f)
    assert len(chunks) >= 1
    assert chunks[0].chunk_type in ("function", "module")


def test_chunk_file_binary_skipped(tmp_path):
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n")
    chunks = chunk_file(f)
    assert chunks == []
