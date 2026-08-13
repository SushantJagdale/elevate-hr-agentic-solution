"""Policy Knowledge Base Service (RAG & OKF Markdown Retrieval Engine)."""

import math
import os
import re
from pathlib import Path
import yaml
from ..config import settings
from ..models.rag import RAGChunkMetadataSchema, PolicyDocument, GroundingResult

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "did", "do", "does", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    "tell", "please", "know", "company", "altostrat"
}


class PolicyKnowledgeService:
    """Hybrid RAG / Open Knowledge Format (OKF) Policy Ingestion & Retrieval Engine."""

    def __init__(self, knowledge_dir: Path | None = None):
        self.knowledge_dir = knowledge_dir or settings.KNOWLEDGE_DIR
        self._chunks: list[RAGChunkMetadataSchema] = []
        self._docs: dict[str, PolicyDocument] = {}
        self._idf: dict[str, float] = {}
        self._load_knowledge_base()

    def _tokenize(self, text: str, filter_stop: bool = False) -> list[str]:
        """Tokenize and normalize text."""
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = [w for w in clean.split() if len(w) > 2]
        if filter_stop:
            tokens = [w for w in tokens if w not in STOPWORDS]
        return tokens

    def _load_knowledge_base(self):
        """Parse all markdown files in the knowledge directory."""
        if not self.knowledge_dir.exists():
            return

        doc_count = 0
        all_terms_in_docs: list[set[str]] = []

        for root, _, files in os.walk(self.knowledge_dir):
            for file in files:
                if not file.endswith(".md"):
                    continue
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    continue

                doc_id = file_path.stem
                category = Path(root).name
                rel_path = file_path.relative_to(self.knowledge_dir)

                # Parse frontmatter if present
                meta = {}
                body = content
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            meta = yaml.safe_load(parts[1]) or {}
                            body = parts[2]
                        except Exception:
                            body = content

                doc_title = meta.get("title") or meta.get("name") or doc_id.replace("-", " ").title()
                
                # Split body into sections by markdown headings
                sections = re.split(r"(?m)^(?=##?#?\s+)", body)
                doc_chunks: list[RAGChunkMetadataSchema] = []

                for idx, sec in enumerate(sections):
                    sec_text = sec.strip()
                    if not sec_text or len(sec_text) < 30:
                        continue

                    # Extract heading
                    first_line = sec_text.splitlines()[0]
                    sec_title = first_line.lstrip("#").strip() if first_line.startswith("#") else doc_title
                    sec_id = f"{doc_id}_{idx+1}"

                    deep_link = f"https://hr.corp/policies/{category}/{file_path.stem}#{sec_title.lower().replace(' ', '-')}"
                    gcs_uri = f"gs://altostrat-hr-policies/{category}/{file_path.name}"

                    chunk = RAGChunkMetadataSchema(
                        document_id=doc_id,
                        document_name=doc_title,
                        section_title=sec_title,
                        section_id=sec_id,
                        gcs_source_uri=gcs_uri,
                        deep_link_url=deep_link,
                        chunk_id=f"chunk_{doc_id}_{idx+1}",
                        chunk_text=sec_text,
                    )
                    self._chunks.append(chunk)
                    doc_chunks.append(chunk)

                    terms = set(self._tokenize(sec_text) + self._tokenize(sec_title) + self._tokenize(doc_title))
                    all_terms_in_docs.append(terms)

                self._docs[doc_id] = PolicyDocument(
                    doc_id=doc_id,
                    title=doc_title,
                    category=category,
                    content=content,
                    file_path=str(rel_path),
                    sections=doc_chunks,
                )
                doc_count += 1

        # Calculate IDF for BM25-like scoring
        total_chunks = len(self._chunks)
        if total_chunks > 0:
            all_vocab = set()
            for s in all_terms_in_docs:
                all_vocab.update(s)

            for term in all_vocab:
                doc_freq = sum(1 for s in all_terms_in_docs if term in s)
                self._idf[term] = math.log((total_chunks - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 4) -> GroundingResult:
        """Search policy knowledge base using BM25-style lexical + title matching."""
        # Key terms without stopwords
        key_tokens = self._tokenize(query, filter_stop=True)
        if not key_tokens:
            key_tokens = self._tokenize(query, filter_stop=False)

        if not key_tokens or not self._chunks:
            return GroundingResult(
                query=query,
                chunks=[],
                attribution_score=0.0,
                is_grounded=False,
                source_citations=[],
            )

        scored_chunks: list[tuple[float, RAGChunkMetadataSchema, int]] = []

        for chunk in self._chunks:
            chunk_tokens = self._tokenize(chunk.chunk_text)
            title_tokens = self._tokenize(chunk.document_name) + self._tokenize(chunk.section_title)

            score = 0.0
            matched_terms = 0

            for q in key_tokens:
                idf = self._idf.get(q, 1.0)
                tf_body = chunk_tokens.count(q)
                tf_title = title_tokens.count(q)

                if tf_body > 0 or tf_title > 0:
                    matched_terms += 1
                    tf_score = (tf_body / (tf_body + 1.5)) + (3.0 * tf_title / (tf_title + 1.0))
                    score += idf * tf_score

            if matched_terms > 0:
                coverage = matched_terms / len(key_tokens)
                final_score = score * (0.4 + 0.6 * coverage)
                scored_chunks.append((final_score, chunk, matched_terms))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_chunks[:top_k]

        if not top_results or top_results[0][0] < 0.5:
            return GroundingResult(
                query=query,
                chunks=[],
                attribution_score=0.0,
                is_grounded=False,
                source_citations=[],
            )

        top_match = top_results[0]
        top_score = top_match[0]
        top_matched_count = top_match[2]
        coverage_ratio = top_matched_count / len(key_tokens)

        # Attribution score calculation: High relevance when core keywords match
        if coverage_ratio >= 0.5 and top_score > 1.5:
            attribution_score = min(0.99, max(0.88, round(0.85 + 0.14 * coverage_ratio, 2)))
        else:
            attribution_score = round(min(0.80, (top_score / 3.0) * coverage_ratio), 2)

        selected_chunks = [item[1] for item in top_results]
        citations = [
            f"[{c.document_name} — {c.section_title}]({c.deep_link_url})"
            for c in selected_chunks
        ]
        unique_citations = list(dict.fromkeys(citations))

        is_grounded = attribution_score >= settings.GROUNDING_ATTRIBUTION_THRESHOLD

        return GroundingResult(
            query=query,
            chunks=selected_chunks,
            attribution_score=attribution_score,
            is_grounded=is_grounded,
            source_citations=unique_citations,
        )

    def list_all_policies(self) -> list[dict]:
        """List summary of available corporate policy documents."""
        return [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "category": d.category,
                "sections_count": len(d.sections),
            }
            for d in self._docs.values()
        ]


policy_service = PolicyKnowledgeService()
