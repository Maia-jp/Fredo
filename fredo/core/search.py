"""Fuzzy search engine for Fredo."""

from typing import List, Optional

from thefuzz import fuzz

from fredo.core.database import db
from fredo.core.models import Snippet


class SearchResult:
    """A search result with score."""

    def __init__(self, snippet: Snippet, score: int):
        """Initialize search result."""
        self.snippet = snippet
        self.score = score

    def __repr__(self):
        """String representation."""
        return f"SearchResult(name={self.snippet.name}, score={self.score})"


class SearchEngine:
    """Fuzzy search engine for snippets."""

    def search(
        self,
        query: Optional[str] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[SearchResult]:
        """Search snippets with fuzzy matching and filters.

        Args:
            query: Search query for fuzzy matching
            language: Filter by language
            tags: Filter by tags
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects sorted by score (descending)
        """
        # Get snippets from database with filters
        snippets = db.search(language=language, tags=tags)

        if not query:
            # No query, just return all matching filters sorted by update time
            results = [SearchResult(s, 100) for s in snippets]
            if limit:
                results = results[:limit]
            return results

        # Calculate fuzzy match scores
        results = []
        for snippet in snippets:
            score = self._calculate_score(query, snippet)
            if score > 0:  # Only include results with some match
                results.append(SearchResult(snippet, score))

        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)

        if limit:
            results = results[:limit]

        return results

    def _calculate_score(self, query: str, snippet: Snippet) -> int:
        """Calculate fuzzy match score for a snippet.

        Scoring strategy:
        - Name exact match: 100
        - Name fuzzy match: weighted by ratio (up to 90)
        - Tag match: 70 per matching tag
        - Content match: weighted by ratio (up to 50)
        """
        query_lower = query.lower()
        name_lower = snippet.name.lower()

        # Check for exact name match
        if query_lower == name_lower:
            return 100

        # Check for name substring match
        if query_lower in name_lower:
            return 95

        # Calculate fuzzy match scores
        name_score = fuzz.ratio(query_lower, name_lower)

        # Check for tag matches
        tag_score = 0
        for tag in snippet.tags:
            if query_lower in tag.lower():
                tag_score += 70
            elif fuzz.ratio(query_lower, tag.lower()) > 80:
                tag_score += 50

        # Calculate content match score
        content_lower = snippet.content.lower()
        if query_lower in content_lower:
            # Count occurrences for relevance
            occurrences = content_lower.count(query_lower)
            content_score = min(50, 20 + (occurrences * 5))
        else:
            # Fuzzy match on first 500 chars of content
            content_preview = content_lower[:500]
            content_fuzzy = fuzz.partial_ratio(query_lower, content_preview)
            content_score = int(content_fuzzy * 0.5)  # Scale down content matches

        # Combine scores with weights
        # Name is most important, then tags, then content
        total_score = max(
            int(name_score * 0.9),  # Name match weighted at 90%
            tag_score,  # Tag matches (can be high)
            content_score,  # Content match (lower weight)
        )

        # Boost score if there are multiple types of matches
        match_types = sum(
            [
                name_score > 60,
                tag_score > 0,
                content_score > 0,
            ]
        )
        if match_types > 1:
            total_score = min(100, int(total_score * 1.1))

        return total_score


# Global search engine instance
search_engine = SearchEngine()

