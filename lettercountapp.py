import streamlit as st
import re
import docx
import PyPDF2

# TXT 파일 텍스트 추출
def extract_text_from_txt(file):
    # 파일을 읽어 문자열로 디코딩
    return file.getvalue().decode("utf-8")

# DOCX 파일 텍스트 추출
def extract_text_from_docx(file):
    doc = docx.Document(file)
    # 문서 내의 모든 단락을 줄바꿈으로 연결
    return "\n".join([para.text for para in doc.paragraphs])

# PDF 파일 텍스트 추출
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# 텍스트 분석 로직
def analyze_text(text):
    # 1. 공백 포함 총 글자 수
    total_chars = len(text)
    
    # 2. 공백 제외 글자 수 (띄어쓰기, 줄바꿈, 탭 제거)
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    
    # 3. 단어 수 (공백 기준으로 분리)
    words = len(text.split())
    
    # 4. 특수문자 수 (정규표현식: 알파벳, 숫자, 한글, 기본 공백이 아닌 문자 카운트)
    # \w: 알파벳, 숫자, 언더스코어(_) / \s: 공백 문자
    # 단, 한글 처리를 위해 완벽히 필터링하려면 정규식을 세밀하게 조정할 수 있습니다.
    special_chars = len(re.findall(r'[^\w\s]', text))
    
    return total_chars, chars_no_spaces, words, special_chars

# --- Streamlit 웹 앱 UI 구성 ---
st.set_page_config(page_title="문서 분석기", page_icon="📝", layout="centered")

st.title("📝 문서 글자 및 특수문자 카운터")
st.markdown("텍스트(TXT), 워드(DOCX), PDF 파일을 업로드하면 텍스트 통계를 분석해 드립니다.")

# 파일 업로드 컴포넌트
uploaded_file = st.file_uploader("파일을 업로드하세요", type=["txt", "docx", "pdf"])

if uploaded_file is not None:
    # 파일 확장자 확인
    file_extension = uploaded_file.name.split('.')[-1].lower()
    text = ""
    
    try:
        # 진행 상태 표시
        with st.spinner('문서를 분석하는 중입니다...'):
            if file_extension == 'txt':
                text = extract_text_from_txt(uploaded_file)
            elif file_extension == 'docx':
                text = extract_text_from_docx(uploaded_file)
            elif file_extension == 'pdf':
                text = extract_text_from_pdf(uploaded_file)
        
        # 텍스트가 정상적으로 추출되었을 경우
        if text.strip():
            st.success("텍스트 분석이 완료되었습니다!")
            
            # 분석 함수 호출
            total_chars, chars_no_spaces, words, special_chars = analyze_text(text)
            
            # 4개의 열로 나누어 결과 표시 (Streamlit Metric 활용)
            st.subheader("📊 분석 결과")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("총 글자 (공백 포함)", f"{total_chars:,}자")
            col2.metric("글자 (공백 제외)", f"{chars_no_spaces:,}자")
            col3.metric("단어 수", f"{words:,}개")
            col4.metric("특수문자", f"{special_chars:,}개")
            
            # 추출된 텍스트 확인을 위한 확장 패널 (기본적으로 접혀있음)
            with st.expander("추출된 원본 텍스트 미리보기"):
                st.text_area("텍스트 내용", text, height=300, disabled=True)
                
        else:
            st.warning("문서에서 텍스트를 찾을 수 없습니다. (이미지로 된 스캔본 PDF일 수 있습니다.)")
            
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")