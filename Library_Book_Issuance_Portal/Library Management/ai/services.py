import json
import logging
import re

from .gemini_client import GeminiUnavailable, generate
from .prompts import (
    CHAT_SYSTEM_PROMPT,
    NL_SEARCH_PROMPT,
    RECOMMEND_PROMPT,
    SUMMARY_PROMPT,
    TAGS_PROMPT,
)

logger = logging.getLogger(__name__)

CATALOG_LIMIT = 40


def _safe_generate(prompt):
    try:
        return generate(prompt)
    except GeminiUnavailable as exc:
        logger.info("Gemini unavailable: %s", exc)
        return ''
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return ''


def _extract_json_array(text):
    if not text:
        return []
    match = re.search(r'\[[^\]]*\]', text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [int(x) for x in data if isinstance(x, (int, float, str)) and str(x).strip().lstrip('-').isdigit()]


def _serialize_catalog(books):
    items = []
    for b in books[:CATALOG_LIMIT]:
        items.append({
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'tags': b.ai_tags or '',
            'summary': (b.ai_summary or b.description or '')[:240],
        })
    return json.dumps(items, ensure_ascii=False)


def summarize_book(description):
    if not description:
        return ''
    return _safe_generate(SUMMARY_PROMPT.format(description=description[:2000]))


def generate_tags(title, description):
    text = _safe_generate(TAGS_PROMPT.format(title=title, description=(description or '')[:2000]))
    if not text:
        return []
    tags = [t.strip().lower() for t in text.replace('\n', ',').split(',') if t.strip()]
    cleaned = []
    for t in tags:
        t = re.sub(r'^[\d\.\-\s]+', '', t).strip(' "\'.')
        if t and t not in cleaned:
            cleaned.append(t)
    return cleaned[:6]


def natural_language_search(query, books_queryset):
    books = list(books_queryset)
    if not books or not query:
        return books
    prompt = NL_SEARCH_PROMPT.format(query=query, catalog=_serialize_catalog(books))
    text = _safe_generate(prompt)
    ids = _extract_json_array(text)
    if not ids:
        q = query.lower()
        return [b for b in books if q in b.title.lower() or q in (b.ai_tags or '').lower() or q in (b.description or '').lower()]
    book_map = {b.id: b for b in books}
    ordered = [book_map[i] for i in ids if i in book_map]
    return ordered


def recommend_for_student(student, limit=5):
    from books.models import Book
    from transactions.models import IssueRecord

    past = (IssueRecord.objects
            .filter(student=student)
            .select_related('book')
            .order_by('-issue_date')[:5])
    past_books = [r.book for r in past]
    past_ids = {b.id for b in past_books}

    available = Book.objects.exclude(id__in=past_ids).filter(available_copies__gt=0)
    if not past_books:
        return list(available[:limit])

    history_text = '\n'.join(
        f"- {b.title} by {b.author} (tags: {b.ai_tags or 'n/a'})" for b in past_books
    )
    prompt = RECOMMEND_PROMPT.format(
        history=history_text,
        catalog=_serialize_catalog(list(available)),
    )
    text = _safe_generate(prompt)
    ids = _extract_json_array(text)
    if ids:
        book_map = {b.id: b for b in available}
        picks = [book_map[i] for i in ids if i in book_map]
        if picks:
            return picks[:limit]

    past_categories = {b.category_id for b in past_books if b.category_id}
    fallback = available.filter(category_id__in=past_categories) if past_categories else available
    return list(fallback[:limit])


def chat_answer(question, student=None):
    from books.models import Book

    if not question or not question.strip():
        return "Please ask me a question about books or the library."

    catalog_books = list(Book.objects.all()[:CATALOG_LIMIT])
    prompt = CHAT_SYSTEM_PROMPT.format(
        catalog=_serialize_catalog(catalog_books),
        question=question.strip(),
    )
    reply = _safe_generate(prompt)
    if not reply:
        return ("The AI assistant is unavailable right now. "
                "Try browsing the catalog or using the search filters.")
    return reply
