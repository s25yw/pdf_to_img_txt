import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
from docx import Document
from docx.shared import Inches, Pt

# 페이지 설정
st.set_page_config(page_title="PDF 추출 및 문서 재조립기", page_icon="⚙️", layout="wide")

st.title("⚙️ PDF 이미지/텍스트 추출 및 재조립 웹 앱")
st.markdown("PDF를 업로드하면 **1) TXT 파일**, **2) JPG 이미지(ZIP)**를 각기 추출하고, 이를 **3) 편집 가능한 문서**로 다시 합성해 드립니다.")

# 파일 업로드
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    extracted_text_all = ""
    all_images = []  # (파일명, 바이너리, PIL 객체, 페이지 번호)
    
    # 합성용 Word 문서 생성
    merged_doc = Document()
    merged_doc.add_heading(f"문서 제목: {uploaded_file.name.rsplit('.', 1)[0]}", level=1)

    with st.spinner("PDF 분석, 텍스트/이미지 추출 및 문서 재조립 진행 중..."):
        img_global_count = 0
        
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            
            # 1. 텍스트 추출
            page_text = page.get_text()
            if page_text.strip():
                extracted_text_all += f"=== [Page {page_num}] ===\n" + page_text + "\n\n"
            
            # 재조립 문서에 페이지 헤더 추가
            merged_doc.add_heading(f"Page {page_num}", level=2)
            if page_text.strip():
                merged_doc.add_paragraph(page_text)
            
            # 2. 이미지 추출
            image_list = page.get_images(full=True)
            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    if pil_img.mode in ("RGBA", "P", "CMYK"):
                        pil_img = pil_img.convert("RGB")
                    
                    jpg_buffer = io.BytesIO()
                    pil_img.save(jpg_buffer, format="JPEG", quality=95)
                    jpg_bytes = jpg_buffer.getvalue()
                    
                    img_global_count += 1
                    img_name = f"image_p{page_num}_{img_global_count}.jpg"
                    all_images.append((img_name, jpg_bytes, pil_img, page_num))
                    
                    # 재조립 문서에 이미지 삽입 (가로 너비 자동 맞춤)
                    img_stream = io.BytesIO(jpg_bytes)
                    merged_doc.add_picture(img_stream, width=Inches(5.5))
                    merged_doc.add_paragraph(f"[삽입된 이미지: {img_name}]")
                except Exception:
                    continue

    st.success("🎉 분석 및 문서 합성 작업이 완료되었습니다!")
    
    # 3개 탭으로 결과 구분
    tab1, tab2, tab3 = st.tabs(["📄 텍스트 (.txt)", "🖼️ 이미지 (.jpg)", "📝 합성 문서 (편집용)"])
    
    # --- Tab 1: 텍스트 추출 결과 ---
    with tab1:
        st.subheader("1. 추출된 텍스트")
        if extracted_text_all.strip():
            txt_filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_text.txt"
            st.download_button(
                label="💾 텍스트 파일(.txt) 다운로드",
                data=extracted_text_all.encode("utf-8"),
                file_name=txt_filename,
                mime="text/plain; charset=utf-8",
                type="primary"
            )
            st.text_area("텍스트 내용 미리보기", extracted_text_all, height=300)
        else:
            st.warning("텍스트를 추출할 수 없습니다.")

    # --- Tab 2: 이미지 추출 결과 ---
    with tab2:
        st.subheader("2. 추출된 이미지")
        if all_images:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for img_name, jpg_bytes, _, _ in all_images:
                    zip_file.writestr(img_name, jpg_bytes)
            zip_buffer.seek(0)
            
            st.download_button(
                label=f"📦 전체 이미지 ZIP 다운로드 ({len(all_images)}개)",
                data=zip_buffer,
                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_images.zip",
                mime="application/zip",
                type="primary"
            )
            
            cols = st.columns(3)
            for idx, (img_name, jpg_bytes, pil_img, p_num) in enumerate(all_images):
                with cols[idx % 3]:
                    st.image(pil_img, caption=f"Page {p_num}: {img_name}", use_container_width=True)
        else:
            st.warning("추출할 이미지가 없습니다.")

    # --- Tab 3: 재조립 문서 결과 ---
    with tab3:
        st.subheader("3. 텍스트 + 이미지 재조립 문서")
        st.info("💡 한컴오피스(한글)는 DOCX 포맷을 완벽 지원합니다. 아래 문서를 다운로드한 뒤 한글에서 열어 `.hwpx`로 바로 저장하실 수 있습니다.")
        
        docx_buffer = io.BytesIO()
        merged_doc.save(docx_buffer)
        docx_buffer.seek(0)
        
        merged_filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_assembled.docx"
        st.download_button(
            label="📝 편집 가능한 문서(.docx) 다운로드",
            data=docx_buffer,
            file_name=merged_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )