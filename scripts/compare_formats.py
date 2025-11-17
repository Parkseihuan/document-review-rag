"""Compare parsing quality across different file formats"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.parsers import PDFParser, DOCParser, DOCXParser, HWPParser


def analyze_text(text, format_name):
    """Analyze parsed text quality"""
    if not text:
        return {
            'format': format_name,
            'success': False,
            'error': 'No text extracted'
        }

    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Count Korean characters
    korean_chars = sum(1 for char in text if '\uAC00' <= char <= '\uD7A3')

    # Count English characters
    english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)

    # Count numbers
    numbers = sum(1 for char in text if char.isdigit())

    # Count special characters
    special_chars = len([c for c in text if not c.isalnum() and not c.isspace()])

    return {
        'format': format_name,
        'success': True,
        'total_chars': len(text),
        'total_lines': len(lines),
        'non_empty_lines': len(non_empty_lines),
        'korean_chars': korean_chars,
        'english_chars': english_chars,
        'numbers': numbers,
        'special_chars': special_chars,
        'words': len(text.split()),
        'avg_line_length': len(text) / len(non_empty_lines) if non_empty_lines else 0
    }


def compare_formats(base_filename):
    """
    Compare parsing results for the same document in different formats

    Args:
        base_filename: Base name without extension (e.g., "고등교육법")
    """
    print("=" * 80)
    print("파일 형식별 인식률 비교")
    print("=" * 80)

    # Define formats and parsers
    formats = {
        '.pdf': PDFParser,
        '.doc': DOCParser,
        '.docx': DOCXParser,
        '.hwp': HWPParser
    }

    results = {}

    # Test each format
    for ext, parser in formats.items():
        file_path = os.path.join(Config.RAW_DATA_DIR, base_filename + ext)

        print(f"\n[{ext.upper()}] {base_filename}{ext}")
        print("-" * 80)

        if not os.path.exists(file_path):
            print(f"  ❌ 파일이 없습니다: {file_path}")
            print(f"     테스트하려면 이 파일을 data/raw/ 폴더에 넣어주세요.")
            results[ext] = {
                'format': ext.upper(),
                'success': False,
                'error': 'File not found'
            }
            continue

        # Parse the file
        try:
            text = parser.parse(file_path)

            if text:
                result = analyze_text(text, ext.upper())
                results[ext] = result

                print(f"  ✅ 파싱 성공")
                print(f"     총 문자 수: {result['total_chars']:,}")
                print(f"     총 줄 수: {result['total_lines']:,}")
                print(f"     내용이 있는 줄: {result['non_empty_lines']:,}")
                print(f"     한글: {result['korean_chars']:,} 글자")
                print(f"     영문: {result['english_chars']:,} 글자")
                print(f"     숫자: {result['numbers']:,} 개")
                print(f"     특수문자: {result['special_chars']:,} 개")
                print(f"     단어 수: {result['words']:,}")
                print(f"     평균 줄 길이: {result['avg_line_length']:.1f} 글자")

                # Show sample text
                sample = text[:200].replace('\n', ' ')
                print(f"\n  📝 샘플 텍스트:")
                print(f"     {sample}...")

            else:
                results[ext] = {
                    'format': ext.upper(),
                    'success': False,
                    'error': 'Parser returned no text'
                }
                print(f"  ❌ 파싱 실패: 텍스트 추출 안 됨")

        except Exception as e:
            results[ext] = {
                'format': ext.upper(),
                'success': False,
                'error': str(e)
            }
            print(f"  ❌ 오류 발생: {e}")

    # Summary comparison
    print("\n" + "=" * 80)
    print("비교 결과 요약")
    print("=" * 80)

    successful_results = {k: v for k, v in results.items() if v.get('success')}

    if not successful_results:
        print("\n⚠️  성공적으로 파싱된 파일이 없습니다.")
        print("\n테스트 방법:")
        print(f"  1. 같은 내용의 문서를 여러 형식으로 준비하세요:")
        print(f"     - {base_filename}.pdf")
        print(f"     - {base_filename}.doc")
        print(f"     - {base_filename}.docx")
        print(f"     - {base_filename}.hwp")
        print(f"  2. data/raw/ 폴더에 복사하세요")
        print(f"  3. 다시 이 스크립트를 실행하세요:")
        print(f"     python scripts/compare_formats.py {base_filename}")
        return

    print(f"\n성공적으로 파싱된 형식: {len(successful_results)}/{len(formats)}\n")

    # Create comparison table
    print(f"{'형식':<8} {'문자수':>10} {'줄수':>8} {'한글':>10} {'영문':>10} {'인식률':>8}")
    print("-" * 80)

    # Find the format with most text (reference)
    max_chars = max(r['total_chars'] for r in successful_results.values())

    for ext in ['.pdf', '.doc', '.docx', '.hwp']:
        if ext in successful_results:
            r = successful_results[ext]
            recognition_rate = (r['total_chars'] / max_chars * 100) if max_chars > 0 else 0

            print(f"{r['format']:<8} {r['total_chars']:>10,} {r['total_lines']:>8,} "
                  f"{r['korean_chars']:>10,} {r['english_chars']:>10,} {recognition_rate:>7.1f}%")
        else:
            print(f"{ext[1:].upper():<8} {'실패':>10} {'-':>8} {'-':>10} {'-':>10} {'-':>8}")

    # Recommendations
    print("\n" + "=" * 80)
    print("💡 권장사항")
    print("=" * 80)

    if len(successful_results) == 0:
        print("\n⚠️  모든 형식이 실패했습니다.")
    elif len(successful_results) == 1:
        best_format = list(successful_results.keys())[0]
        print(f"\n✅ {best_format.upper()}만 성공: 이 형식을 사용하세요.")
    else:
        # Find best format (most text extracted)
        best_format = max(successful_results.items(), key=lambda x: x[1]['total_chars'])
        worst_format = min(successful_results.items(), key=lambda x: x[1]['total_chars'])

        best_ext, best_result = best_format
        worst_ext, worst_result = worst_format

        print(f"\n🥇 가장 좋음: {best_ext.upper()}")
        print(f"   - {best_result['total_chars']:,} 글자 추출")
        print(f"   - 한글: {best_result['korean_chars']:,}, 영문: {best_result['english_chars']:,}")

        if best_ext != worst_ext:
            diff = best_result['total_chars'] - worst_result['total_chars']
            diff_percent = (diff / best_result['total_chars'] * 100) if best_result['total_chars'] > 0 else 0

            print(f"\n📊 {worst_ext.upper()}과 비교:")
            print(f"   - {diff:,} 글자 더 추출 ({diff_percent:.1f}% 차이)")

        # Specific recommendations
        print(f"\n✅ 권장 형식: {best_ext.upper()}")

        # Check if differences are significant
        char_counts = [r['total_chars'] for r in successful_results.values()]
        max_diff_percent = (max(char_counts) - min(char_counts)) / max(char_counts) * 100 if max(char_counts) > 0 else 0

        if max_diff_percent < 5:
            print("   (모든 형식이 비슷하게 잘 작동합니다. 편한 형식을 사용하세요.)")
        elif max_diff_percent < 15:
            print("   (약간의 차이가 있습니다. 최상의 결과를 위해 이 형식을 권장합니다.)")
        else:
            print("   (형식 간 차이가 큽니다. 이 형식을 사용하는 것을 강력히 권장합니다.)")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='파일 형식별 인식률 비교',
        epilog="""
사용 예시:
  python scripts/compare_formats.py 고등교육법

테스트 준비:
  1. 같은 내용의 문서를 여러 형식으로 저장
  2. data/raw/ 폴더에 복사
     - 고등교육법.pdf
     - 고등교육법.doc
     - 고등교육법.docx
     - 고등교육법.hwp
  3. 스크립트 실행
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('filename', nargs='?',
                       help='테스트할 파일명 (확장자 제외, 예: 고등교육법)')

    args = parser.parse_args()

    if not args.filename:
        print("사용법: python scripts/compare_formats.py <파일명>")
        print("\n예시: python scripts/compare_formats.py 고등교육법")
        print("\n준비사항:")
        print("  data/raw/ 폴더에 같은 내용의 파일을 여러 형식으로 준비:")
        print("  - 고등교육법.pdf")
        print("  - 고등교육법.doc")
        print("  - 고등교육법.docx")
        print("  - 고등교육법.hwp")
        return

    compare_formats(args.filename)


if __name__ == "__main__":
    main()
