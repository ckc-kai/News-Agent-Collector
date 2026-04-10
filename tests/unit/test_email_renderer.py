"""Tests for EmailRenderer — inline-style HTML digest email (TDD RED phase)."""

from datetime import date

import pytest

from src.app.services.email_renderer import EmailRenderer


SAMPLE_ITEMS = [
    {
        "title": "AI Takes Over Silicon Valley",
        "summary": "A two-paragraph summary about AI trends.",
        "domain": "ai_ml",
        "source_url": "https://techcrunch.com/ai-article",
        "source_name": "event_registry",
        "published_at": "Apr 09, 10:00",
        "article_id": "abc123",
    },
    {
        "title": "Climate Report Published",
        "summary": "New climate data released by scientists.",
        "domain": "science",
        "source_url": "https://science.org/climate",
        "source_name": "arxiv",
        "published_at": "Apr 09, 08:00",
        "article_id": "def456",
    },
]


class TestEmailRenderer:
    def setup_method(self):
        self.renderer = EmailRenderer()

    def test_subject_contains_date(self):
        subject, _, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "Apr 9" in subject or "April 9" in subject or "2026" in subject

    def test_html_contains_first_article_title(self):
        _, html, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "AI Takes Over Silicon Valley" in html

    def test_html_contains_second_article_title(self):
        _, html, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "Climate Report Published" in html

    def test_html_contains_article_summary(self):
        _, html, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "two-paragraph summary" in html

    def test_html_contains_read_link(self):
        _, html, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "https://techcrunch.com/ai-article" in html

    def test_html_uses_no_style_tags(self):
        """Gmail strips <style> blocks — renderer must use inline styles only."""
        _, html, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "<style" not in html
        assert "<link" not in html

    def test_html_is_valid_document(self):
        _, html, _ = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "<html" in html
        assert "</html>" in html

    def test_text_fallback_contains_title(self):
        _, _, text = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "AI Takes Over Silicon Valley" in text

    def test_text_fallback_contains_url(self):
        _, _, text = self.renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "https://techcrunch.com/ai-article" in text

    def test_empty_items_returns_valid_html(self):
        _, html, _ = self.renderer.render([], sent_date=date(2026, 4, 9))
        assert "<html" in html


class TestEmailRendererClickTracking:
    """Article links are wrapped via Cloudflare Worker when worker_url is configured."""

    def test_url_wrapped_when_worker_url_set(self):
        """Links go through Worker redirect when worker_url is provided."""
        renderer = EmailRenderer(worker_url="https://tracker.example.workers.dev")
        _, html, _ = renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "tracker.example.workers.dev/click/abc123" in html

    def test_url_direct_when_no_worker_url(self):
        """Links are unchanged when no worker_url is configured."""
        renderer = EmailRenderer()
        _, html, _ = renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        assert "https://techcrunch.com/ai-article" in html

    def test_redirect_url_encodes_target(self):
        """Redirect URL includes the original URL as a query parameter."""
        renderer = EmailRenderer(worker_url="https://tracker.example.workers.dev")
        _, html, _ = renderer.render(SAMPLE_ITEMS, sent_date=date(2026, 4, 9))
        # The original URL must be present (encoded) in the redirect
        assert "techcrunch.com" in html
