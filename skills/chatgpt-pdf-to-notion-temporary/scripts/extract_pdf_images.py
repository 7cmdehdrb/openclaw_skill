#!/usr/bin/env python3
import argparse
from pathlib import Path

import fitz  # PyMuPDF


def extract_images_from_pdf(pdf_path_str: str) -> int:
    pdf_path = Path(pdf_path_str)

    # 1) 파일 확인
    if not pdf_path.exists() or not pdf_path.is_file():
        print(f"오류: 파일을 찾을 수 없습니다 -> {pdf_path}")
        return 0

    if pdf_path.suffix.lower() != ".pdf":
        print("오류: PDF 파일만 지원합니다.")
        return 0

    # 2) 저장 폴더 생성 (원본 파일명 기준)
    output_dir = pdf_path.parent / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"폴더 생성 완료: {output_dir}")

    extracted_count = 0

    # 3) PDF 이미지 추출
    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                image_name = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                image_filepath = output_dir / image_name

                with open(image_filepath, "wb") as f:
                    f.write(image_bytes)

                extracted_count += 1

        doc.close()
        print(f"작업 완료: 총 {extracted_count}개의 이미지를 성공적으로 추출했습니다.")

    except Exception as e:
        print(f"이미지 추출 중 오류가 발생했습니다: {e}")

    return extracted_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF 파일에서 이미지를 추출하여 폴더에 저장합니다.")
    parser.add_argument("pdf_path", help="처리할 PDF 파일의 절대 경로나 상대 경로")
    args = parser.parse_args()

    extract_images_from_pdf(args.pdf_path)
