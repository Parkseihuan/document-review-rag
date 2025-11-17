"""TXT file parser"""
from typing import Optional


class TXTParser:
    """Parse TXT files to markdown"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """
        Parse TXT file and extract text

        Args:
            file_path: Path to TXT file

        Returns:
            Text content in markdown format or None if parsing fails
        """
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()

                    # Successfully read with this encoding
                    if not content.strip():
                        return "# Empty Document\n\nThis text file is empty."

                    # Convert to markdown format
                    markdown = f"# {file_path.split('/')[-1].replace('.txt', '')}\n\n{content}"
                    return markdown

                except UnicodeDecodeError:
                    continue  # Try next encoding

            # If all encodings fail
            print(f"Error: Could not decode {file_path} with any encoding")
            return None

        except Exception as e:
            print(f"Error parsing TXT {file_path}: {e}")
            return None

    @staticmethod
    def to_markdown(file_path: str, output_path: str) -> bool:
        """
        Parse TXT and save as markdown file

        Args:
            file_path: Path to TXT file
            output_path: Path to save markdown file

        Returns:
            True if successful, False otherwise
        """
        content = TXTParser.parse(file_path)
        if content:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing markdown file: {e}")
                return False
        return False
