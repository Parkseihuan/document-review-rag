"""Text chunking for RAG processing"""
from typing import List, Dict
import os
import re


class TextChunker:
    """Split text into chunks for embedding"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize text chunker

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using recursive character text splitting

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []

        # Try each separator in order
        for separator in self.separators:
            if separator == "":
                # Last resort: split by character
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                    chunk = text[i:i + self.chunk_size]
                    if chunk:
                        chunks.append(chunk)
                break

            if separator in text:
                parts = text.split(separator)
                current_chunk = ""

                for part in parts:
                    if len(current_chunk) + len(part) + len(separator) <= self.chunk_size:
                        current_chunk += part + separator
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())

                        # If single part is too large, recursively split it
                        if len(part) > self.chunk_size:
                            sub_chunks = self._split_text(part)
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part + separator

                if current_chunk:
                    chunks.append(current_chunk.strip())
                break

        # Add overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_chunk = chunks[i-1]
                curr_chunk = chunks[i]
                overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                overlapped_chunks.append(overlap_text + " " + curr_chunk)
            return overlapped_chunks

        return chunks

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks

        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = self._split_text(text)
        result = []

        for i, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk,
                'chunk_index': i,
                'total_chunks': len(chunks),
            }
            if metadata:
                chunk_data.update(metadata)
            result.append(chunk_data)

        return result

    def chunk_file(self, file_path: str) -> List[Dict]:
        """
        Read and chunk a text/markdown file

        Args:
            file_path: Path to the file

        Returns:
            List of chunk dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            metadata = {
                'source': os.path.basename(file_path),
                'file_path': file_path,
            }

            return self.chunk_text(text, metadata)

        except Exception as e:
            print(f"Error chunking file {file_path}: {e}")
            return []

    def chunk_directory(self, directory: str, extension: str = '.md') -> List[Dict]:
        """
        Chunk all files in a directory

        Args:
            directory: Directory containing files
            extension: File extension to process

        Returns:
            List of all chunks from all files
        """
        all_chunks = []

        for filename in os.listdir(directory):
            if filename.endswith(extension):
                file_path = os.path.join(directory, filename)
                chunks = self.chunk_file(file_path)
                all_chunks.extend(chunks)
                print(f"Chunked {filename}: {len(chunks)} chunks")

        return all_chunks
