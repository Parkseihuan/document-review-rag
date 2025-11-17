"""PDF file parser"""
import PyPDF2
from typing import Optional


class PDFParser:
    """Parse PDF files to markdown"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """
        Parse PDF file and extract text

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text in markdown format or None if parsing fails
        """
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_content = []

                # Extract text from each page
                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"## Page {page_num}\n\n{text}\n")

                markdown = '\n'.join(text_content)
                return markdown

        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return None

    @staticmethod
    def to_markdown(file_path: str, output_path: str) -> bool:
        """
        Parse PDF and save as markdown file

        Args:
            file_path: Path to PDF file
            output_path: Path to save markdown file

        Returns:
            True if successful, False otherwise
        """
        content = PDFParser.parse(file_path)
        if content:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing markdown file: {e}")
                return False
        return False
