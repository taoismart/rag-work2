from fastapi import APIRouter

import logging
from typing import Dict, List, Any
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ParseService:

    def __init__(self):
        self.title_patterns = [
            r'^第[一二三四五六七八九十百千万]+[章节篇]',  # 中文章节标题
            r'^\d+\.\s+[^\n]+',  # 数字编号标题 (如: 1. 标题)
            r'^[A-Z]\.\s+[^\n]+',  # 字母编号标题 (如: A. 标题)
            r'^\d+\)\s+[^\n]+',  # 数字括号标题 (如: 1) 标题)
            r'^[A-Z]\)\s+[^\n]+',  # 字母括号标题 (如: A) 标题)
            r'^（\d+）\s*[^\n]+',  # 中文括号数字标题 (如: （1）标题)
            r'^（[一二三四五六七八九十]+）\s*[^\n]+',  # 中文括号中文数字标题 (如: （一）标题)
            r'^[一二三四五六七八九十]+、\s*[^\n]+',  # 中文顿号标题 (如: 一、标题)
            r'^[（(][一二三四五六七八九十]+[）)]\s*[^\n]+',  # 中文括号标题 (如: （一）标题 或 (一)标题)
            r'^[（(][A-Z][）)]\s*[^\n]+',  # 中文括号字母标题 (如: （A）标题 或 (A)标题)
        ]

    def parse_pdf(self, text: str, method: str, metadata: dict, page_map: list = None) -> dict:

        try:
            
            parsed_content = []
            total_pages = len(page_map)
            
            if method == "all_text":
                parsed_content = self._parse_all_text(page_map)
            elif method == "by_pages":
                parsed_content = self._parse_by_pages(page_map)
            elif method == "by_titles":
                parsed_content = self._parse_by_titles(page_map)
            elif method == "text_and_tables":
                parsed_content = self._parse_text_and_tables(page_map)
            else:
                raise ValueError(f"Unsupported parsing method: {method}")
                
            # Create document-level metadata
            document_data = {
                "metadata": {
                    "filename": metadata.get("filename", ""),
                    "total_pages": total_pages,
                    "parsing_method": method,
                    "timestamp": datetime.now().isoformat()
                },
                "content": parsed_content
            }
            
            return document_data
        
        
            
        except Exception as e:
            logger.error(f"Error in parse_pdf: {str(e)}")
            raise

    def _parse_all_text(self, page_map: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析所有文本，将所有页面的文本合并成一个完整的文本块
        """
        try:
            # 合并所有页面的文本
            full_text = "\n".join(page["text"] for page in page_map)
            
            return [{
                "type": "Text",
                "content": full_text,
                "page": 1  # 由于是完整文本，页码设为1
            }]
            
        except Exception as e:
            logger.error(f"解析所有文本失败: {str(e)}")
            raise
            

    def _parse_by_pages(self, page_map: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按页面解析文本
        """
        try:
            parsed_content = []
            
            for page in page_map:
                page_content = {
                    "type": "page",
                    "page_number": page['page'],
                    "content": page['text'],
                    "word_count": len([char for char in page['text'] if char.strip()])
                }
                parsed_content.append(page_content)
            
            return parsed_content
            
        except Exception as e:
            logger.error(f"按页面解析失败: {str(e)}")
            raise

    def _parse_by_titles(self, page_map: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按标题解析文本
        """
        try:
            parsed_content = []
            current_section = None
            current_content = []
            first_title_found = False
            
            for page in page_map:
                text = page['text']
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 检查是否是标题
                    if any(re.match(pattern, line) for pattern in self.title_patterns):
                        # 如果是第一个标题，保存之前的内容
                        if not first_title_found and current_content:
                            parsed_content.append({
                                "type": "section",
                                "title": "前言",
                                "content": "\n".join(current_content),
                                "page": page['page']
                            })
                            first_title_found = True
                        # 保存前一个章节
                        elif current_section:
                            parsed_content.append({
                                "type": "section",
                                "title": current_section,
                                "content": "\n".join(current_content),
                                "page": page['page']
                            })
                        
                        # 开始新章节
                        current_section = line
                        current_content = []
                    else:
                        current_content.append(line)
            
            # 保存最后一个章节
            if current_section:
                parsed_content.append({
                    "type": "section",
                    "title": current_section,
                    "content": "\n".join(current_content),
                    "page": page['page']
                })
            # 如果整个文档都没有标题，将所有内容作为前言
            elif current_content and not first_title_found:
                parsed_content.append({
                    "type": "section",
                    "title": "前言",
                    "content": "\n".join(current_content),
                    "page": page['page']
                })
            
            return parsed_content
            
        except Exception as e:
            logger.error(f"按标题解析失败: {str(e)}")
            raise

    def _parse_text_and_tables(self, page_map: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析文本和表格
        """
        try:
            parsed_content = []
            
            for page in page_map:
                text = page['text']
                lines = text.split('\n')
                
                # 检测表格（简单实现：连续的行包含多个制表符或空格）
                table_lines = []
                current_paragraph = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 检查是否是表格行（包含多个制表符或连续空格）
                    if re.search(r'\t|\s{2,}', line):
                        # 如果有未处理的段落，先保存
                        if current_paragraph:
                            parsed_content.append({
                                "type": "paragraph",
                                "content": "\n".join(current_paragraph),
                                "page": page['page']
                            })
                            current_paragraph = []
                        
                        # 处理表格行
                        cells = re.split(r'\t|\s{2,}', line)
                        table_lines.append([cell.strip() for cell in cells if cell.strip()])
                    else:
                        # 如果有未处理的表格，先保存
                        if table_lines:
                            parsed_content.append({
                                "type": "table",
                                "rows": table_lines,
                                "page": page['page']
                            })
                            table_lines = []
                        
                        current_paragraph.append(line)
                
                # 保存最后的段落或表格
                if current_paragraph:
                    parsed_content.append({
                        "type": "paragraph",
                        "content": "\n".join(current_paragraph),
                        "page": page['page']
                    })
                elif table_lines:
                    parsed_content.append({
                        "type": "table",
                        "rows": table_lines,
                        "page": page['page']
                    })
            
            return parsed_content
            
        except Exception as e:
            logger.error(f"解析文本和表格失败: {str(e)}")
            raise

   