from fastapi import APIRouter, FastAPI, UploadFile, File, Form, HTTPException, Body, Query, Request, Depends
from services.load_service import LoadService
from services.chunk_service import ChunkService
from services.parse_service import ParseService
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建服务实例
load_service = LoadService()
chunk_service = ChunkService()
parse_service = ParseService()

@router.post("/load")
async def load(   
    file: UploadFile = File(...),
    loading_method: str = Form(...),
    strategy: str = Form(None),
    chunking_strategy: str = Form(None),
    chunking_options: str = Form(None)
):
    try:
        # 保存上传的文件
        temp_path = os.path.join("temp", file.filename)
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 准备元数据
        metadata = {
            "filename": file.filename,
            "total_chunks": 0,  
            "total_pages": 0,   
            "loading_method": loading_method,
            "loading_strategy": strategy,  
            "chunking_strategy": chunking_strategy, 
            "timestamp": datetime.now().isoformat()
        }
        
        chunking_options_dict = None
        if chunking_options:
            chunking_options_dict = json.loads(chunking_options)
        
        loading_service = LoadService()
        raw_text = loading_service.load_pdf(
            temp_path, 
            loading_method, 
            strategy=strategy,
            chunking_strategy=chunking_strategy,
            chunking_options=chunking_options_dict
        )
        
        metadata["total_pages"] = loading_service.get_total_pages()
        
        page_map = loading_service.get_page_map()
        
        chunks = []
        for idx, page in enumerate(page_map, 1):
            # 统计字数（同时支持中英文）
            text = page["text"]
            word_count = len([char for char in text if char.strip()])  # 去除空白字符后统计字符数
            
            chunk_metadata = {
                "chunk_id": idx,
                "page_number": page["page"],
                "page_range": str(page["page"]),
                "word_count": word_count
            }
            if "metadata" in page:
                chunk_metadata.update(page["metadata"])
            
            chunks.append({
                "content": page["text"],
                "metadata": chunk_metadata
            })
        
        filepath = loading_service.save_document(
            filename=file.filename,
            chunks=chunks,
            metadata=metadata,
            loading_method=loading_method,
            strategy=strategy,
            chunking_strategy=chunking_strategy,
        )
        
        with open(filepath, "r", encoding="utf-8") as f:
            document_data = json.load(f)
        
        # 清理临时文件
        os.remove(temp_path)
        
        return {"loaded_content": document_data, "filepath": filepath}
    except Exception as e:
        logger.error(f"加载错误: {str(e)}")
        raise
    

@router.post("/chunk")
async def chunk_document(data: dict = Body(...)):
    try:
        doc_id = data.get("doc_id")
        chunking_option = data.get("chunking_option")
        chunk_size = data.get("chunk_size", 1000)
        print(f"doc_id: {data}")
        print(f"chunking_option: {chunking_option}")
        print(f"chunk_size: {chunk_size}")
        
        if not doc_id or not chunking_option:
            raise HTTPException(
                status_code=400, 
                detail="参数错误: doc_id 和 chunking_option 不能为空"
            )
        
        # 读取已加载的文档
        file_path = os.path.join("01-loaded-docs", doc_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文档不存在")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            
        # 构建页面映射
        page_map = [
            {
                'page': chunk['metadata']['page_number'],
                'text': chunk['content']
            }
            for chunk in doc_data['chunks']
        ]
            
        # 准备元数据
        metadata = {
            "filename": doc_data['filename'],
            "loading_method": doc_data['loading_method'],
            "total_pages": doc_data['total_pages']
        }
            
        chunking_service = ChunkService()
        result = chunking_service.chunk_text(
            text="", 
            method=chunking_option,
            metadata=metadata,
            page_map=page_map,
            chunk_size=chunk_size
        )
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        base_name = doc_data['filename'].replace('.pdf', '').split('_')[0]
        output_filename = f"{base_name}_{chunking_option}_{timestamp}.json"
        
        output_path = os.path.join("01-chunked-docs", output_filename)
        os.makedirs("01-chunked-docs", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
        
    except Exception as e:
        logger.error(f"分块错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse")
async def parse(
    file: UploadFile = File(...),
    loading_method: str = Form(...),
    strategy: str = Form(None),
    chunking_strategy: str = Form(None),
    chunking_options: str = Form(None)
):
    try:
        # 保存上传的文件
        temp_path = os.path.join("temp", file.filename)
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 准备元数据
        metadata = {
            "filename": file.filename,
            "total_pages": 0,
            "loading_method": loading_method,
            "loading_strategy": strategy,
            "timestamp": datetime.now().isoformat()
        }
        
        # 使用 LoadService 加载和解析 PDF
        loading_service = LoadService()
        chunking_options_dict = None
        if chunking_options:
            chunking_options_dict = json.loads(chunking_options)
            
        raw_text = loading_service.load_pdf(
            temp_path, 
            loading_method, 
            strategy=strategy,
            chunking_strategy=chunking_strategy,
            chunking_options=chunking_options_dict
        )
        
        metadata["total_pages"] = loading_service.get_total_pages()
        page_map = loading_service.get_page_map()
        
        # 使用 ParseService 进行解析
        parse_service = ParseService()
        parsed_result = parse_service.parse_pdf(
            text=raw_text,
            method=chunking_strategy,
            metadata=metadata,
            page_map=page_map
        )
        
        # 清理临时文件
        os.remove(temp_path)
        
        return parsed_result
        
    except Exception as e:
        logger.error(f"解析错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/loaded-docs")
async def get_loaded_docs():
    try:
        docs_dir = "01-loaded-docs"
        if not os.path.exists(docs_dir):
            return []
            
        documents = []
        for filename in os.listdir(docs_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(docs_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        documents.append({
                            "filename": doc_data.get("filename", filename),
                            "filepath": filename
                        })
                except Exception as e:
                    logger.error(f"读取文件 {filename} 失败: {str(e)}")
                    continue
                    
        return documents
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 