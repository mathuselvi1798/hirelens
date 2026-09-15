"""Parsing is deterministic, so it gets deterministic tests.

If these break, every downstream analysis silently degrades - which is exactly
why this layer is tested first.
"""
from app.documents import structure
from tests.conftest import RESUME_TEXT


def test_detects_standard_sections():
    names = [s.name for s in structure.detect_sections(RESUME_TEXT)]
    assert "summary" in names
    assert "experience" in names
    assert "education" in names
    assert "skills" in names


def test_section_content_stops_at_next_heading():
    sections = {s.name: s for s in structure.detect_sections(RESUME_TEXT)}
    assert "Anna University" in sections["education"].content
    assert "Anna University" not in sections["skills"].content


def test_extracts_bullets():
    bullets = structure.extract_bullets(RESUME_TEXT)
    assert len(bullets) == 5
    assert bullets[0].startswith("Cut p95 API latency")


def test_extracts_contact_details():
    contact = structure.extract_contact(RESUME_TEXT)
    assert contact.email == "karthik@example.com"
    assert contact.phone is not None
    assert any("linkedin" in link for link in contact.links)


def test_headings_are_not_confused_with_sentences():
    text = "My experience includes building large systems for many clients."
    assert structure.detect_sections(text) == []


def test_word_count_is_reasonable():
    assert structure.count_words(RESUME_TEXT) > 50
