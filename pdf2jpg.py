import streamlit as st
import fitz  # PyMuPDF 라이브러리
from PIL import Image
import io
import zipfile

# 페이지 설정
st.set_page_config(page_title="PDF 이미지 추출기", page_icon="🖼️", layout="centered")

st.title("🖼️ PDF 이미지 추출기 (PDF to JPG)")
st.markdown("PDF 파일을 업로드하면 문서 내부의 이미지를 찾아 **JPG 형식**으로 추출해 드립니다.")

# 파일 업로더
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    # PDF 파일 읽기
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    extracted_images = []  # (파일명, JPG 바이너리 데이터, PIL Image 객체)
    
    with st.spinner("PDF 문서에서 이미지를 추출하는 중입니다..."):
        img_count = 0
        for page_index in range(len(doc)):
            page = doc[page_index]
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]  # 이미지 객체 참조 ID
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                try:
                    # PIL을 사용해 이미지 열기 및 RGB 변환 (JPG 저장 대비)
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    if pil_img.mode in ("RGBA", "P", "CMYK"):
                        pil_img = pil_img.convert("RGB")
                    
                    # JPG 포맷으로 메모리 내 저장
                    jpg_buffer = io.BytesIO()
                    pil_img.save(jpg_buffer, format="JPEG", quality=95)
                    jpg_bytes = jpg_buffer.getvalue()
                    
                    img_count += 1
                    img_filename = f"image_page{page_index + 1}_{img_count}.jpg"
                    extracted_images.append((img_filename, jpg_bytes, pil_img))
                except Exception:
                    # 호환되지 않거나 손상된 이미지 스킵
                    continue

    if extracted_images:
        st.success(f"🎉 총 {len(extracted_images)}개의 이미지를 성공적으로 추출했습니다!")
        
        # 1. 전체 이미지를 ZIP 파일로 압축
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for img_name, jpg_bytes, _ in extracted_images:
                zip_file.writestr(img_name, jpg_bytes)
        
        zip_buffer.seek(0)
        
        # ZIP 전체 다운로드 버튼
        st.download_button(
            label="📦 모든 이미지 ZIP으로 한번에 다운로드",
            data=zip_buffer,
            file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_extracted_images.zip",
            mime="application/zip",
            type="primary"
        )
        
        st.divider()
        
        # 2. 이미지 미리보기 및 개별 다운로드
        st.subheader("🖼️ 추출된 이미지 미리보기 및 개별 다운로드")
        
        # 2열 레이아웃으로 배치
        cols = st.columns(2)
        for idx, (img_name, jpg_bytes, pil_img) in enumerate(extracted_images):
            col = cols[idx % 2]
            with col:
                st.image(pil_img, caption=img_name, use_container_width=True)
                st.download_button(
                    label=f"⬇️ {img_name} 다운로드",
                    data=jpg_bytes,
                    file_name=img_name,
                    mime="image/jpeg",
                    key=f"dl_btn_{idx}"
                )
    else:
        st.warning("업로드된 PDF 파일에서 추출 가능한 이미지를 찾을 수 없습니다.")