import streamlit as st
import pdfplumber
import io

# 페이지 설정
st.set_page_config(page_title="PDF 텍스트 추출기", page_icon="📄", layout="centered")

st.title("📄 PDF 텍스트 추출기 (PDF to TXT)")
st.markdown("PDF 파일을 업로드하면 문서 내 텍스트를 추출하여 **.txt 파일**로 저장해 드립니다.")

# 파일 업로더
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    extracted_text = ""
    page_count = 0
    
    with st.spinner("PDF 문서에서 텍스트를 추출하는 중입니다..."):
        try:
            # pdfplumber를 사용하여 메모리 내 PDF 파일 열기
            with pdfplumber.open(uploaded_file) as pdf:
                page_count = len(pdf.pages)
                for idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        # 페이지 구분선과 함께 텍스트 병합
                        extracted_text += f"--- [Page {idx + 1}] ---\n"
                        extracted_text += page_text + "\n\n"
        except Exception as e:
            st.error(f"PDF 처리 중 오류가 발생했습니다: {e}")

    # 텍스트가 정상적으로 추출된 경우
    if extracted_text.strip():
        st.success(f"🎉 총 {page_count}페이지 문서에서 텍스트 추출을 완료했습니다!")
        
        # 텍스트 통계 표시
        char_count = len(extracted_text)
        word_count = len(extracted_text.split())
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 페이지 수", f"{page_count}장")
        col2.metric("총 글자 수 (공백 포함)", f"{char_count:,}자")
        col3.metric("총 단어 수", f"{word_count:,}개")
        
        st.divider()
        
        # TXT 파일 다운로드 버튼
        txt_filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_extracted.txt"
        
        st.download_button(
            label="💾 추출된 텍스트(.txt) 파일 다운로드",
            data=extracted_text.encode('utf-8'),
            file_name=txt_filename,
            mime="text/plain; charset=utf-8",
            type="primary"
        )
        
        # 미리보기
        with st.expander("👀 추출된 텍스트 미리보기"):
            st.text_area("텍스트 내용", extracted_text, height=350)
            
    else:
        st.warning("⚠️ 문서에서 추출할 수 있는 텍스트를 찾지 못했습니다. (텍스트가 포함되지 않은 단순 스캔 이미지 PDF일 수 있습니다.)")