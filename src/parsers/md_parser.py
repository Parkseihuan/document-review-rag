"""MD (Markdown) file parser"""
from typing import Optional
import os


class MDParser:
    """Parse MD (Markdown) files"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """
        Parse MD file (already in markdown format)

        Args:
            file_path: Path to MD file

        Returns:
            Markdown content or None if parsing fails
        """
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()

                    # MD files are already in markdown format
                    # Just ensure it has a title
                    if not content.startswith('#'):
                        filename = os.path.basename(file_path).replace('.md', '')
                        content = f"# {filename}\n\n{content}"

                    return content

                except UnicodeDecodeError:
                    continue

            # All encodings failed
            print(f"  ❌ Could not read {file_path} with any encoding")
            return None

        except Exception as e:
            print(f"  ❌ Error reading MD file {file_path}: {e}")
            return None

    @staticmethod
    def to_markdown(file_path: str, output_path: str) -> bool:
        """
        Copy MD file to markdown directory

        Args:
            file_path: Path to MD file
            output_path: Path to save markdown file

        Returns:
            True if successful, False otherwise
        """
        content = MDParser.parse(file_path)
        if content:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing markdown file: {e}")
                return False
        return False
