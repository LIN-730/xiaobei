# tools/knowledge_tools.py — RAG 知识库查询工具 (工厂模式)
"""
Knowledge/RAG 相关工具。
使用工厂模式创建：create_knowledge_tools(user_id, db_session, upload_dir) → list[BaseTool]。
每个用户可独立初始化 RAGManager，实现多租户隔离。
"""
from __future__ import annotations

from typing import Optional

from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

# ── 软导入 RAGManager（如未安装依赖则优雅降级） ──
try:
    from knowledge.rag import RAGManager as _RAGManager
except ImportError:
    _RAGManager = None


def _create_manager(
    user_id: str,
    upload_dir: Optional[str] = None,
) -> Optional[object]:
    """
    创建 RAGManager 实例。
    如依赖缺失则返回 None，工具将提示功能未启用。
    """
    if _RAGManager is None:
        return None
    kwargs = {"user_id": user_id}
    if upload_dir:
        kwargs["upload_dir"] = upload_dir
    return _RAGManager(**kwargs)


async def _search_knowledge_base(rag_manager, query: str) -> str:
    """
    搜索已上传的知识库文档（培养方案/课程资料/课件/考试资料等）。
    当用户询问课程内容、考试范围、培养方案细节、或其他可能在已上传文档中的信息时使用。

    Args:
        query: 搜索关键词或问题

    Returns:
        匹配的文档片段文本
    """
    if rag_manager is None:
        return "知识库功能未启用（缺少 RAG 依赖或未初始化）。"

    try:
        results = rag_manager.retrieve(query, top_k=5)

        if not results:
            return "知识库中没有找到相关内容。你可以上传相关的课程资料、培养方案等文件，我会学习后回答。"

        context = ""
        for r in results:
            context += f"\n【{r.get('source', '未知')} ({r.get('category', '')})】\n{r['text'][:400]}\n"

        return f"在知识库中找到 {len(results)} 条相关内容：\n{context}"

    except Exception as e:
        return f"知识库搜索失败：{e}（可能还没有上传文件，或向量数据库未初始化）"


async def _list_knowledge_files(rag_manager) -> str:
    """列出知识库中已上传的所有文件及其分类。"""
    if rag_manager is None:
        return "知识库功能未启用（缺少 RAG 依赖或未初始化）。"

    try:
        stats = rag_manager.get_stats()
        sources = stats.get("sources", [])

        if not sources:
            return "知识库中没有文件。你可以通过应用上传课程资料、培养方案、课件等文件。"

        result = f"知识库共有 {stats['total_chunks']} 个文本块，{len(sources)} 个文件：\n"
        for s in sources:
            result += f"  [{s.get('category', '未分类')}] {s['source']} ({s['chunks']}块)\n"

        cats = stats.get("categories", {})
        if cats:
            result += "\n分类分布："
            for cat, count in cats.items():
                result += f" {cat}({count})"
        return result

    except Exception as e:
        return f"知识库查询失败：{e}"


def create_knowledge_tools(
    user_id: str,
    db_session: AsyncSession,
    upload_dir: Optional[str] = None,
) -> list:
    """
    创建知识库相关 Tool 列表（工厂模式）。

    每个用户的 RAGManager 独立初始化，参数绑定在闭包中。

    Args:
        user_id: 当前用户 UUID（用于 RAG 多租户隔离）
        db_session: 异步数据库会话
        upload_dir: 文件上传目录（可选，传给 RAGManager）

    Returns:
        list[BaseTool]: 知识库相关 Tool 列表，可能为空列表（缺少 RAG 依赖时）
    """
    rag_manager = _create_manager(user_id, upload_dir)

    # 闭包绑定 rag_manager
    async def _bound_search(query: str = "", **kwargs):
        return await _search_knowledge_base(rag_manager, query)
    _bound_search.__name__ = "search_knowledge_base_bound"

    async def _bound_list(**kwargs):
        return await _list_knowledge_files(rag_manager)
    _bound_list.__name__ = "list_knowledge_files_bound"

    # 包装为 Tool
    t_search = StructuredTool.from_function(
        name="search_knowledge_base",
        description=(
            "搜索已上传的知识库文档(培养方案/课程资料/课件/考试资料等)。参数: query(搜索关键词)。"
            "触发: 「培养方案里对学分有什么要求」「课件关于XX讲了什么」等。"
        ),
        coroutine=_bound_search,
        infer_schema=False,
    )

    t_list = StructuredTool.from_function(
        name="list_knowledge_files",
        description=(
            "列出知识库中已上传的所有文件及其分类。无参数。"
            "触发: 「知识库有什么文件」「已上传了什么资料」等。"
        ),
        coroutine=_bound_list,
        infer_schema=False,
    )

    return [t_search, t_list]
