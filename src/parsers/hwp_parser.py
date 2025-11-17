"""HWP file parser"""
import os
import sys
from typing import Optional

try:
    from pyhwp import HWPReader
except ImportError:
    HWPReader = None


class HWPParser:
    """Parse HWP (한글) files to markdown"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """
        Parse HWP file and extract text

        Args:
            file_path: Path to HWP file

        Returns:
            Extracted text in markdown format or None if parsing fails
        """
        if HWPReader is None:
            # Try alternative methods
            return HWPParser._parse_alternative(file_path)

        try:
            # Try using pyhwp
            hwp = HWPReader(file_path)
            text_content = []

            for paragraph in hwp.paragraphs():
                text = paragraph.get_text().strip()
                if text:
                    text_content.append(f"{text}\n")

            return '\n'.join(text_content)

        except Exception as e:
            print(f"  pyhwp failed: {e}")
            return HWPParser._parse_alternative(file_path)

    @staticmethod
    def _parse_alternative(file_path: str) -> Optional[str]:
        """
        Alternative parsing methods for HWP files

        Tries multiple methods:
        1. HWP 5.0+ (ZIP-based XML)
        2. HWP 3.0/5.0 (OLE2-based)
        3. Windows COM (if Hangul is installed)

        Args:
            file_path: Path to HWP file

        Returns:
            Extracted text or None if parsing fails
        """
        # Method 1: Try HWP 5.0+ (ZIP-based)
        result = HWPParser._parse_hwp5(file_path)
        if result:
            return result

        # Method 2: Try HWP 3.0/5.0 (OLE2-based)
        result = HWPParser._parse_ole2(file_path)
        if result:
            return result

        # Method 3: Try Windows COM
        if sys.platform == 'win32':
            result = HWPParser._parse_com(file_path)
            if result:
                return result

        # All methods failed
        print(f"  ❌ Could not parse {os.path.basename(file_path)}")
        print(f"     HWP 파일을 읽을 수 없습니다. 다음 방법을 시도하세요:")
        print(f"     1. HWP를 DOCX로 변환: 한글에서 열기 → 다른 형식으로 저장 → DOCX")
        print(f"     2. HWP를 PDF로 변환: 한글에서 열기 → PDF로 저장")
        print(f"     3. pywin32 설치: pip install pywin32 (한글 프로그램 필요)")
        return None

    @staticmethod
    def _parse_hwp5(file_path: str) -> Optional[str]:
        """
        Parse HWP 5.0+ files (ZIP-based XML format)

        Args:
            file_path: Path to HWP file

        Returns:
            Extracted text or None
        """
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(file_path, 'r') as zf:
                # List files in the ZIP
                file_list = zf.namelist()

                # Look for section files
                section_files = [f for f in file_list if f.startswith('Contents/section')]
                section_files.sort()

                text_content = []

                for section_file in section_files:
                    try:
                        with zf.open(section_file) as f:
                            xml_content = f.read()
                            root = ET.fromstring(xml_content)

                            # Extract text from XML
                            # HWP 5.0+ uses specific tags for text content
                            for elem in root.iter():
                                # Look for text elements
                                if elem.text and elem.text.strip():
                                    text_content.append(elem.text.strip())

                    except Exception as e:
                        print(f"    Warning: Error parsing section {section_file}: {e}")
                        continue

                if text_content:
                    filename = os.path.basename(file_path).replace('.hwp', '')
                    markdown = f"# {filename}\n\n" + '\n\n'.join(text_content)
                    return markdown

        except zipfile.BadZipFile:
            # Not a ZIP file, try OLE2 method
            pass
        except Exception as e:
            print(f"    HWP 5.0+ parsing failed: {e}")

        return None

    @staticmethod
    def _parse_ole2(file_path: str) -> Optional[str]:
        """
        Parse HWP 3.0/5.0 files (OLE2-based format)

        Args:
            file_path: Path to HWP file

        Returns:
            Extracted text or None
        """
        try:
            import olefile
            import zlib

            f = olefile.OleFileIO(file_path)
            dirs = f.listdir()

            # Find BodyText sections
            text_content = []
            for dir_name in dirs:
                if dir_name[0] == "BodyText":
                    stream = f.openstream(dir_name)
                    data = stream.read()

                    # Try to decompress if needed
                    try:
                        unpacked = zlib.decompress(data, -15)
                        text = unpacked.decode('utf-16-le', errors='ignore')
                    except:
                        text = data.decode('utf-16-le', errors='ignore')

                    # Clean up text
                    text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t ')
                    if text.strip():
                        text_content.append(text)

            f.close()

            if text_content:
                filename = os.path.basename(file_path).replace('.hwp', '')
                markdown = f"# {filename}\n\n" + '\n\n'.join(text_content)
                return markdown

        except Exception as e:
            print(f"    OLE2 parsing failed: {e}")

        return None

    @staticmethod
    def _parse_com(file_path: str) -> Optional[str]:
        """
        Parse HWP using Windows COM (requires Hangul Word Processor installed)

        Args:
            file_path: Path to HWP file

        Returns:
            Extracted text or None
        """
        try:
            import win32com.client

            hwp = None
            try:
                # Create Hangul application
                hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
                hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")

                # Open document (correct parameter format)
                abs_path = os.path.abspath(file_path)
                hwp.Open(abs_path)

                # Get entire text using different method
                ctrl = hwp.HeadCtrl
                text_content = []

                # Try to get all text
                hwp.InitScan(option=0)

                while True:
                    state, text = hwp.GetText()
                    if state == 1:  # End of document
                        break
                    if text.strip():
                        text_content.append(text.strip())

                # Alternative: Get text from body
                if not text_content:
                    try:
                        hwp.Run("SelectAll")
                        hwp.Run("Copy")
                        # Text should be in clipboard but hard to get from Python
                    except:
                        pass

                if text_content:
                    filename = os.path.basename(file_path).replace('.hwp', '')
                    markdown = f"# {filename}\n\n" + '\n\n'.join(text_content)
                    return markdown

            finally:
                if hwp:
                    try:
                        hwp.Clear(1)
                    except:
                        pass
                    try:
                        hwp.Quit()
                    except:
                        pass

        except ImportError:
            print(f"    pywin32 not installed")
        except Exception as e:
            print(f"    COM parsing failed: {e}")

        return None

    @staticmethod
    def to_markdown(file_path: str, output_path: str) -> bool:
        """
        Parse HWP and save as markdown file

        Args:
            file_path: Path to HWP file
            output_path: Path to save markdown file

        Returns:
            True if successful, False otherwise
        """
        content = HWPParser.parse(file_path)
        if content:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing markdown file: {e}")
                return False
        return False
