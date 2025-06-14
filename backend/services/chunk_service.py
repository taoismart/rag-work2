from fastapi import APIRouter
from datetime import datetime
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter

router = APIRouter()
logger = logging.getLogger(__name__)

class ChunkService:
    
    def chunk_text(self, text: str, method: str, metadata: dict, page_map: list = None, chunk_size: int = None) -> dict:
        try:
            chunks = []
            total_pages = len(page_map)
            print(f"method: {method}")
            
            def count_words(text: str) -> int:
                return len([char for char in text if char.strip()])
            
            if method == "by_pages":
                for page_data in page_map:
                    chunk_metadata = {
                        "chunk_id": len(chunks) + 1,
                        "page_number": page_data['page'],
                        "page_range": str(page_data['page']),
                        "word_count": count_words(page_data['text'])
                    }
                    chunks.append({
                        "content": page_data['text'],
                        "metadata": chunk_metadata
                    })
            
            elif method == "fixed_size":
                for page_data in page_map:
                    page_chunks = self._fixed_size_chunks(page_data['text'], chunk_size)
                    for idx, chunk in enumerate(page_chunks, 1):
                        chunk_metadata = {
                            "chunk_id": len(chunks) + 1,
                            "page_number": page_data['page'],
                            "page_range": str(page_data['page']),
                            "word_count": count_words(chunk["text"])
                        }
                        chunks.append({
                            "content": chunk["text"],
                            "metadata": chunk_metadata
                        })
            
            elif method in ["by_paragraphs", "by_sentences"]:
                splitter_method = self._paragraph_chunks if method == "by_paragraphs" else self._sentence_chunks
                for page_data in page_map:
                    page_chunks = splitter_method(page_data['text'])
                    for chunk in page_chunks:
                        chunk_metadata = {
                            "chunk_id": len(chunks) + 1,
                            "page_number": page_data['page'],
                            "page_range": str(page_data['page']),
                            "word_count": count_words(chunk["text"])
                        }
                        chunks.append({
                            "content": chunk["text"],
                            "metadata": chunk_metadata
                        })
            else:
                raise ValueError(f"Unsupported chunking method: {method}")

            # 创建标准化的文档数据结构
            document_data = {
                "filename": metadata.get("filename", ""),
                "total_chunks": len(chunks),
                "total_pages": total_pages,
                "loading_method": metadata.get("loading_method", ""),
                "chunking_method": method,
                "timestamp": datetime.now().isoformat(),
                "chunks": chunks
            }
            
            return document_data
            
        except Exception as e:
            logger.error(f"Error in chunk_text: {str(e)}")
            raise

    def _fixed_size_chunks(self, text: str, chunk_size: int = 1000) -> list:
        """
        将文本按固定大小分块
        :param text: 输入文本
        :param chunk_size: 每个块的大小（字符数）
        :return: 分块列表
        """
        chunks = []
        current_chunk = ""
        words = text.split()
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= chunk_size:
                current_chunk += " " + word if current_chunk else word
            else:
                if current_chunk:
                    chunks.append({"text": current_chunk.strip()})
                current_chunk = word
        
        if current_chunk:
            chunks.append({"text": current_chunk.strip()})
            
        return chunks

    def _paragraph_chunks(self, text: str) -> list:
        """
        将文本按段落分块
        :param text: 输入文本
        :return: 分块列表
        """
        paragraphs = text.split('\n ')
        chunks = []
        
        for para in paragraphs:
            if para.strip():  # 忽略空段落
                chunks.append({"text": para.strip()})
                
        return chunks

    def _sentence_chunks(self, text: str) -> list[dict]:
        """
        将文本按句子分块
        
        Args:
            text: 要分块的文本
            
        Returns:
            分块后的句子列表
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["。", "！", "？", ".", "!", "?", "\n", " "]
        )
        texts = splitter.split_text(text)
        return [{"text": t} for t in texts]