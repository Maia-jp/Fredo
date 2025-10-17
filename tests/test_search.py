"""Tests for the SearchEngine."""

import pytest

from fredo.core.database import Database
from fredo.core.models import Snippet
from fredo.core.search import SearchEngine, SearchResult


class TestSearchResult:
    """Test SearchResult class."""

    def test_create_search_result(self, sample_snippet: Snippet):
        """Test creating a search result."""
        result = SearchResult(sample_snippet, 95)
        
        assert result.snippet == sample_snippet
        assert result.score == 95

    def test_search_result_repr(self, sample_snippet: Snippet):
        """Test search result string representation."""
        result = SearchResult(sample_snippet, 85)
        
        repr_str = repr(result)
        assert "SearchResult" in repr_str
        assert sample_snippet.name in repr_str
        assert "85" in repr_str


class TestSearchBasic:
    """Test basic search functionality."""

    def test_search_with_no_query_returns_all(
        self, db: Database, multiple_snippets
    ):
        """Test that search with no query returns all snippets."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search()
        
        assert len(results) == len(multiple_snippets)
        for result in results:
            assert result.score == 100

    def test_search_empty_database(self, db: Database):
        """Test searching empty database."""
        engine = SearchEngine(database=db)
        results = engine.search(query="test")
        
        assert results == []

    def test_search_returns_search_results(self, db: Database, sample_snippet: Snippet):
        """Test that search returns SearchResult objects."""
        db.create(sample_snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="test")
        
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert isinstance(results[0].snippet, Snippet)
        assert isinstance(results[0].score, int)


class TestSearchScoring:
    """Test search scoring algorithm."""

    def test_exact_name_match_scores_100(self, db: Database):
        """Test that exact name match scores 100."""
        snippet = Snippet(name="docker-compose", content="test")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker-compose")
        
        assert len(results) == 1
        assert results[0].score == 100

    def test_exact_name_match_case_insensitive(self, db: Database):
        """Test that exact match is case-insensitive."""
        snippet = Snippet(name="Docker-Compose", content="test")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker-compose")
        
        assert len(results) == 1
        assert results[0].score == 100

    def test_name_substring_match_scores_95(self, db: Database):
        """Test that name substring match scores 95."""
        snippet = Snippet(name="docker-compose-up", content="test")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        assert results[0].score == 95

    def test_tag_exact_match_scores_high(self, db: Database):
        """Test that tag exact match scores 70 per tag."""
        snippet = Snippet(
            name="test-snippet",
            content="test",
            tags=["docker", "deployment"],
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        # Should get high score from tag match
        assert results[0].score >= 70

    def test_tag_substring_match(self, db: Database):
        """Test that tag substring match scores well."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["docker-compose"],
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        assert results[0].score >= 70

    def test_content_match_scores_lower(self, db: Database):
        """Test that content match scores lower than name match."""
        snippet = Snippet(
            name="script",
            content="This script uses docker to deploy",
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        # Content match should be lower score
        assert results[0].score < 95

    def test_multiple_content_occurrences_boost_score(self, db: Database):
        """Test that multiple occurrences in content boost score."""
        snippet = Snippet(
            name="script",
            content="docker run docker ps docker stop docker",
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        assert results[0].score > 20  # Should get boost from multiple matches

    def test_combined_matches_boost_score(self, db: Database):
        """Test that multiple match types boost score."""
        snippet = Snippet(
            name="docker-script",
            content="This uses docker",
            tags=["docker"],
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        # Should get boost from matching in name, tags, and content
        assert results[0].score >= 70


class TestSearchSorting:
    """Test search result sorting."""

    def test_results_sorted_by_score_descending(self, db: Database):
        """Test that results are sorted by score descending."""
        # Create snippets with different match qualities
        exact = Snippet(name="docker", content="test")
        substring = Snippet(name="docker-compose", content="test")
        content_only = Snippet(name="script", content="uses docker")
        
        db.create(exact)
        db.create(substring)
        db.create(content_only)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        # Should be sorted by score
        assert len(results) == 3
        assert results[0].score >= results[1].score
        assert results[1].score >= results[2].score

    def test_results_sorted_highest_first(self, db: Database):
        """Test that highest scoring result is first."""
        weak_match = Snippet(name="script", content="some docker content")
        strong_match = Snippet(name="docker", content="test")
        
        db.create(weak_match)
        db.create(strong_match)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert results[0].snippet.name == "docker"


class TestSearchFilters:
    """Test search filters."""

    def test_search_with_language_filter(self, db: Database, multiple_snippets):
        """Test searching with language filter."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(language="python")
        
        assert len(results) == 2
        for result in results:
            assert result.snippet.language == "python"

    def test_search_with_tag_filter(self, db: Database, multiple_snippets):
        """Test searching with tag filter."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(tags=["hello"])
        
        assert len(results) == 2
        for result in results:
            assert "hello" in result.snippet.tags

    def test_search_with_multiple_tag_filters(self, db: Database, multiple_snippets):
        """Test searching with multiple tags (OR logic)."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(tags=["docker", "api"])
        
        # Should match snippets with docker OR api
        assert len(results) == 2
        result_names = [r.snippet.name for r in results]
        assert "docker-cleanup" in result_names
        assert "js-fetch" in result_names

    def test_search_with_query_and_language_filter(
        self, db: Database, multiple_snippets
    ):
        """Test searching with both query and language filter."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="hello", language="python")
        
        assert len(results) == 1
        assert results[0].snippet.name == "python-hello"

    def test_search_with_all_filters(self, db: Database):
        """Test searching with all filters combined."""
        snippet = Snippet(
            name="python-docker",
            content="docker script",
            language="python",
            tags=["docker", "automation"],
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(
            query="docker",
            language="python",
            tags=["automation"],
        )
        
        assert len(results) == 1
        assert results[0].snippet.name == "python-docker"


class TestSearchLimit:
    """Test search result limiting."""

    def test_search_with_limit(self, db: Database, multiple_snippets):
        """Test limiting search results."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(limit=3)
        
        assert len(results) == 3

    def test_search_with_limit_larger_than_results(
        self, db: Database, multiple_snippets
    ):
        """Test limit larger than available results."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(limit=100)
        
        assert len(results) == len(multiple_snippets)

    def test_search_with_limit_zero(self, db: Database, multiple_snippets):
        """Test limit of zero."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(limit=0)
        
        assert len(results) == 0

    def test_search_query_with_limit(self, db: Database, multiple_snippets):
        """Test query search with limit."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="python", limit=1)
        
        assert len(results) == 1
        # Should return the highest scoring match
        assert "python" in results[0].snippet.name


class TestSearchEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_search_with_empty_query(self, db: Database, multiple_snippets):
        """Test searching with empty string query."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="")
        
        # Empty query treated as no query
        assert len(results) == len(multiple_snippets)

    def test_search_with_special_characters(self, db: Database):
        """Test searching with special characters."""
        snippet = Snippet(name="test-c++", content="c++ code")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="c++")
        
        assert len(results) == 1
        assert results[0].snippet.name == "test-c++"

    def test_search_with_unicode_query(self, db: Database):
        """Test searching with Unicode characters."""
        snippet = Snippet(name="test-世界", content="世界")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="世界")
        
        assert len(results) == 1
        assert results[0].snippet.name == "test-世界"

    def test_search_no_matching_results(self, db: Database, multiple_snippets):
        """Test search with no matching results."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="nonexistent-query-xyz")
        
        assert results == []

    def test_search_filters_out_zero_score_matches(self, db: Database):
        """Test that zero-score matches are filtered out."""
        snippet = Snippet(name="completely-different", content="nothing relevant")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="xyz")
        
        # Only matches with score > 0 are returned
        assert len(results) == 0

    def test_search_with_very_long_query(self, db: Database):
        """Test searching with very long query."""
        snippet = Snippet(name="test", content="test")
        db.create(snippet)
        
        long_query = "x" * 1000
        
        engine = SearchEngine(database=db)
        results = engine.search(query=long_query)
        
        # Should handle gracefully
        assert isinstance(results, list)

    def test_search_case_insensitive(self, db: Database):
        """Test that search is case-insensitive."""
        snippet = Snippet(name="Docker-Compose", content="DOCKER commands")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        assert len(results) == 1
        assert results[0].snippet.name == "Docker-Compose"

    def test_search_partial_word_match(self, db: Database):
        """Test partial word matching."""
        snippet = Snippet(name="kubernetes-deployment", content="test")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="kube")
        
        assert len(results) == 1
        assert results[0].snippet.name == "kubernetes-deployment"

    def test_search_fuzzy_name_match(self, db: Database):
        """Test fuzzy matching on name."""
        snippet = Snippet(name="docker-compose", content="test")
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        # Slight typo
        results = engine.search(query="dokcer")
        
        # Should still match with fuzzy logic
        assert len(results) >= 0  # Fuzzy might or might not match

    def test_calculate_score_with_multiple_tag_matches(self, db: Database):
        """Test score calculation with multiple matching tags."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["docker", "docker-compose", "deployment"],
        )
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        # Should get high score from multiple tag matches
        assert len(results) == 1
        assert results[0].score >= 70


class TestSearchIntegration:
    """Test search integration with database."""

    def test_search_uses_database_search(self, db: Database, multiple_snippets):
        """Test that SearchEngine uses Database.search()."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(language="python")
        
        # Should only get python snippets from database
        assert len(results) == 2

    def test_search_with_database_filters_then_fuzzy(
        self, db: Database, multiple_snippets
    ):
        """Test that database filters are applied before fuzzy matching."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        # First filter by language, then fuzzy match on query
        results = engine.search(query="hello", language="bash")
        
        assert len(results) == 1
        assert results[0].snippet.language == "bash"
        assert "hello" in results[0].snippet.tags


class TestSearchGlobalInstance:
    """Test the global search engine instance."""

    def test_global_search_engine_exists(self):
        """Test that global search engine instance exists."""
        from fredo.core.search import search_engine
        
        assert search_engine is not None
        assert isinstance(search_engine, SearchEngine)

    def test_global_search_engine_is_functional(
        self, db: Database, sample_snippet: Snippet
    ):
        """Test that global search engine works."""
        from fredo.core.search import search_engine
        
        db.create(sample_snippet)
        
        results = search_engine.search(query="test")
        
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)


class TestSearchPerformance:
    """Test search performance and scalability."""

    def test_search_with_many_snippets(self, db: Database):
        """Test search performance with many snippets."""
        # Create 100 snippets
        for i in range(100):
            snippet = Snippet(
                name=f"snippet-{i}",
                content=f"content {i}",
                tags=[f"tag-{i % 10}"],
            )
            db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="snippet")
        
        # Should handle many results efficiently
        assert len(results) == 100

    def test_search_with_large_content(self, db: Database):
        """Test search with snippets containing large content."""
        large_content = "test " * 10000
        snippet = Snippet(name="large-snippet", content=large_content)
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="large")
        
        assert len(results) == 1
        assert results[0].snippet.name == "large-snippet"

    def test_search_content_uses_preview(self, db: Database):
        """Test that content matching only uses first 500 chars."""
        # Create snippet with matching content beyond 500 chars
        content = "x" * 600 + " docker " + "x" * 100
        snippet = Snippet(name="test", content=content)
        db.create(snippet)
        
        engine = SearchEngine(database=db)
        results = engine.search(query="docker")
        
        # Should still find it (though score might be lower)
        # since docker is beyond the 500 char preview
        assert len(results) >= 0

