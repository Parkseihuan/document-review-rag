"""DOC (legacy Word) file parser"""
from typing import Optional
import os
import sys


class DOCParser:
    """Parse legacy DOC files to markdown"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """
        Parse DOC file and extract text

        Args:
            file_path: Path to DOC file

        Returns:
            Text content in markdown format or None if parsing fails
        """
        filename = os.path.basename(file_path).replace('.doc', '')

        # Method 1: Try python-docx (some .doc files are actually .docx)
        try:
            from docx import Document
            doc = Document(file_path)
            text_content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            if text_content:
                markdown = f"# {filename}\n\n" + '\n\n'.join(text_content)
                return markdown
        except Exception:
            pass  # Try next method

        # Method 2: Try Windows Word COM (Windows only, requires MS Word)
        if sys.platform == 'win32':
            try:
                import win32com.client

                word = None
                doc = None
                try:
                    # Create Word application
                    word = win32com.client.Dispatch("Word.Application")
                    word.Visible = False

                    # Open document
                    abs_path = os.path.abspath(file_path)
                    doc = word.Documents.Open(abs_path)

                    # Extract text
                    text = doc.Content.Text

                    if text.strip():
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        markdown = f"# {filename}\n\n" + '\n\n'.join(lines)
                        return markdown

                finally:
                    # Clean up
                    if doc:
                        doc.Close(False)
                    if word:
                        word.Quit()

            except ImportError:
                print(f"  ℹ️  pywin32 not installed (optional for .doc files)")
            except Exception as e:
                print(f"  ⚠️  Word COM failed: {e}")

        # All methods failed
        print(f"  ❌ Could not parse {file_path}")
        print(f"     .doc files can be read with:")
        print(f"     1. Install pywin32: pip install pywin32 (Windows only)")
        print(f"     2. Or convert to .docx format (recommended)")
        print(f"        - Open in Word → Save As → .docx")
        return None

    @staticmethod
    def to_markdown(file_path: str, output_path: str) -> bool:
        """
        Parse DOC and save as markdown file

        Args:
            file_path: Path to DOC file
            output_path: Path to save markdown file

        Returns:
            True if successful, False otherwise
        """
        content = DOCParser.parse(file_path)
        if content:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing markdown file: {e}")
                return False
        return False
