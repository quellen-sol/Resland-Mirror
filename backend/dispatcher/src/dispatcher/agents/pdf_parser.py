from shared.pdfdoc import PdfDoc

from ..doc_parsers.pdf import (
    block_sequence,
    column_counts,
    raw_text,
    whitespace_map,
)
from .docx_parser import (
    PDF_AGENT_PARSER_SYSTEM_PROMPT,
    build_agent_from_views,
)


def agent_parse_pdf(doc: PdfDoc):
    agent_output = build_pdf_resume_agent(doc)
    print("Starting agent...")
    agent_output.agent.invoke(
        {"messages": [{"role": "user", "content": "Parse this document"}]}
    )
    print("Agent finished")
    return agent_output.profile_queue


def build_pdf_resume_agent(doc: PdfDoc):
    """pdf resume agent — same agent, views produced by the pdf parser."""
    return build_agent_from_views(
        doc_raw_text=raw_text(doc),
        doc_block_sequence=block_sequence(doc),
        doc_whitespace_map=whitespace_map(doc),
        doc_column_counts=column_counts(doc),
        system_prompt=PDF_AGENT_PARSER_SYSTEM_PROMPT,
    )
