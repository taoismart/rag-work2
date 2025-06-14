from pypdf import PdfReader
from unstructured.partition.pdf import partition_pdf
import pdfplumber
import fitz  # PyMuPDF
import logging
import os
from datetime import datetime
import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import PyPDF2

logger = logging.getLogger(__name__)

class LoadService:
    def __init__(self):
        self.total_pages = 0
        self.current_page_map = []

    def get_total_pages(self):
        return self.total_pages

    def get_page_map(self):
        return self.current_page_map

    def load_pdf(self, pdf_path, method="pymupdf", strategy=None, chunking_strategy=None, chunking_options=None):
        print(f"加载PDF文件: {pdf_path}")
        print(f"加载方法: {method}")
        print(f"加载策略: {strategy}")
        print(f"分块策略: {chunking_strategy}")
        print(f"分块选项: {chunking_options}")
        try:
            if method == "pymupdf":
                return self._load_with_pymupdf(pdf_path)
            elif method == "pypdf":
                return self._load_with_pypdf(pdf_path)
            elif method == "pdfplumber":
                return self._load_with_pdfplumber(pdf_path)
            elif method == "unstructured":
                return self._load_with_unstructured(
                    pdf_path, 
                    strategy=strategy,
                    chunking_strategy=chunking_strategy,
                    chunking_options=chunking_options
                )
            elif method == "pdfminer":
                return self._load_with_pdfminer(pdf_path)
            else:
                raise ValueError(f"未识别的方法: {method}")
        except Exception as e:
            logger.error(f"加载失败 {method}: {str(e)}")
            raise


    def _load_with_pymupdf(self, pdf_path):
        try:
            with fitz.open(pdf_path) as doc:
                self.total_pages = len(doc)
                self.current_page_map = []
                for page_num, page in enumerate(doc, 1):
                    text = page.get_text().strip()
                    self.current_page_map.append({
                        "page": page_num,
                        "text": text
                    })
                return {"message": f"使用pymupdf加载成功，总页数: {self.total_pages}"}
        except Exception as e:
            logger.error(f"使用pymupdf加载失败: {str(e)}")
            raise

    def _load_with_pypdf(self, pdf_path):
        try:
            with PdfReader(pdf_path) as reader:
                self.total_pages = len(reader.pages)
                self.current_page_map = []
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text().strip()
                    self.current_page_map.append({
                        "page": page_num,
                        "text": text
                    })
                return {"message": f"使用pypdf加载成功，总页数: {self.total_pages}"}
        except Exception as e:
            logger.error(f"使用pypdf加载失败: {str(e)}")
            raise

    def _load_with_pdfplumber(self, pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                self.total_pages = len(pdf.pages)
                self.current_page_map = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text().strip()
                    self.current_page_map.append({
                        "page": page_num,
                        "text": text
                    })
                return {"message": f"使用pdfplumber加载成功，总页数: {self.total_pages}"}
        except Exception as e:
            logger.error(f"使用pdfplumber加载失败: {str(e)}")
            raise

    def _load_with_unstructured(self, pdf_path, strategy=None, chunking_strategy=None, chunking_options=None):
        try:
            # 首先尝试使用PyPDF2获取基本信息
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                self.total_pages = len(pdf_reader.pages)
                
                # 初始化页面映射
                self.current_page_map = []
                
                # 提取每页文本
                for page_num in range(self.total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    self.current_page_map.append({
                        "page": page_num + 1,
                        "text": text.strip()
                    })
                
                return {"message": f"使用PyPDF2加载成功，总页数: {self.total_pages}"}
                
        except Exception as e:
            logger.error(f"使用PyPDF2加载失败: {str(e)}")
            # 如果PyPDF2失败，尝试使用unstructured
            try:
                elements = partition_pdf(
                    filename=pdf_path,
                    strategy="auto",
                    include_page_breaks=True,
                    include_metadata=True,
                    encoding="utf-8"
                )
                
                if not elements:
                    raise ValueError("未能从PDF中提取到任何内容")
                
                self.total_pages = max([elem.metadata.page_number for elem in elements if hasattr(elem, 'metadata')])
                self.current_page_map = []
                
                for page_num in range(1, self.total_pages + 1):
                    page_elements = [elem for elem in elements if hasattr(elem, 'metadata') and elem.metadata.page_number == page_num]
                    page_text = " ".join([elem.text for elem in page_elements if hasattr(elem, 'text')]).strip()
                    
                    self.current_page_map.append({
                        "page": page_num,
                        "text": page_text
                    })
                
                return {"message": f"使用unstructured加载成功，总页数: {self.total_pages}"}
            except Exception as e2:
                logger.error(f"使用unstructured加载也失败: {str(e2)}")
                raise Exception(f"PDF加载失败: {str(e)}")


    def _load_with_pdfminer(self, pdf_path):
        try:
            self.current_page_map = []
            page_texts = {}
            
            # 遍历每一页
            for page_num, page_layout in enumerate(extract_pages(pdf_path), 1):
                page_text = []
                # 提取页面中的文本
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        page_text.append(element.get_text())
                
                page_texts[page_num] = " ".join(page_text).strip()
            
            self.total_pages = len(page_texts)
            self.current_page_map = [
                {"page": num, "text": text}
                for num, text in sorted(page_texts.items())
            ]
            
            return {"message": f"使用pdfminer加载成功，总页数: {self.total_pages}"}
        except Exception as e:
            logger.error(f"使用pdfminer加载失败: {str(e)}")
            raise

    def save_document(self, filename: str, chunks: list, metadata: dict, loading_method: str, strategy: str = None, chunking_strategy: str = None) -> str:
        """
        保存处理后的文档数据。

        参数:
            filename (str): 原PDF文件名
            chunks (list): 文档分块列表
            metadata (dict): 文档元数据
            loading_method (str): 使用的加载方法
            strategy (str, optional): 使用的加载策略
            chunking_strategy (str, optional): 使用的分块策略

        返回:
            str: 保存的文件路径
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            base_name = filename.replace('.pdf', '').split('_')[0]
            
            # Adjust the document name to include strategy if unstructured
            if loading_method == "unstructured" and strategy:
                doc_name = f"{base_name}_{loading_method}_{strategy}_{chunking_strategy}_{timestamp}"
            else:
                doc_name = f"{base_name}_{loading_method}_{timestamp}"
            
            document_data = {
                "filename": str(filename),
                "total_chunks": int(len(chunks)),
                "total_pages": int(metadata.get("total_pages", 1)),
                "loading_method": str(loading_method),
                "loading_strategy": str(strategy) if loading_method == "unstructured" and strategy else None,
                "chunking_strategy": str(chunking_strategy) if loading_method == "unstructured" and chunking_strategy else None,
                "chunking_method": "loaded",
                "timestamp": datetime.now().isoformat(),
                "chunks": chunks
            }
            
            filepath = os.path.join("01-loaded-docs", f"{doc_name}.json")
            os.makedirs("01-loaded-docs", exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, ensure_ascii=False, indent=2)
                
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise