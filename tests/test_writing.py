"""Tests for paper writing."""

import pytest
from thesiskit.writing import Paper, PaperBuilder, PaperSection


def test_paper_section():
    """Test paper section creation."""
    section = PaperSection(
        title="Introduction",
        content="This is the introduction.",
        level=1,
    )
    assert section.title == "Introduction"
    assert section.level == 1


def test_paper_builder():
    """Test paper builder."""
    paper = (
        PaperBuilder()
        .set_title("Test Paper")
        .add_author("John Doe")
        .set_abstract("This is a test abstract.")
        .add_section("Introduction", "Intro content", level=1)
        .add_section("Methods", "Methods content", level=1)
        .add_reference("doe2024")
        .build()
    )
    
    assert paper.title == "Test Paper"
    assert len(paper.authors) == 1
    assert len(paper.sections) == 2
    assert len(paper.references) == 1


def test_paper_to_markdown():
    """Test paper Markdown export."""
    paper = Paper(
        title="Test Paper",
        authors=["John Doe"],
        abstract="Test abstract",
        sections=[
            PaperSection("Introduction", "Intro", 1),
        ],
        references=["ref1"],
    )
    
    md = paper.to_markdown()
    assert "# Test Paper" in md
    assert "John Doe" in md
    assert "## Abstract" in md
    assert "# Introduction" in md  # Section uses # for level 1


def test_paper_builder_validation():
    """Test paper builder validation."""
    builder = PaperBuilder()
    
    with pytest.raises(ValueError, match="Title is required"):
        builder.build()
    
    builder.set_title("Test")
    with pytest.raises(ValueError, match="At least one author"):
        builder.build()
    
    builder.add_author("John")
    with pytest.raises(ValueError, match="Abstract is required"):
        builder.build()
