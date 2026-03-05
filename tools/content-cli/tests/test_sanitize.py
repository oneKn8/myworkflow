"""Tests for markdown sanitization."""

from myworkflow.sanitize import (
    _strip_imports,
    _strip_mdx_components,
    _convert_callouts,
    sanitize_for_devto,
)


def test_strip_imports():
    text = """import { Component } from './component'
import React from 'react'

# Hello World

Some content here."""
    result = _strip_imports(text)
    assert "import" not in result
    assert "# Hello World" in result
    assert "Some content here." in result


def test_strip_mdx_self_closing():
    text = "Before <MyComponent prop='value' /> After"
    result = _strip_mdx_components(text)
    assert "Before" in result
    assert "After" in result
    assert "<MyComponent" not in result


def test_strip_mdx_with_children():
    text = "Before <Wrapper>inner content</Wrapper> After"
    result = _strip_mdx_components(text)
    assert "inner content" in result
    assert "<Wrapper>" not in result


def test_convert_callouts():
    text = """:::note
This is a note.
:::"""
    result = _convert_callouts(text)
    assert "> **Note:**" in result
    assert "This is a note." in result


def test_sanitize_for_devto_full():
    body = """import { Code } from './code'

# My Post

Some <Widget /> content here.

:::warning
Be careful!
:::

The end."""

    result = sanitize_for_devto(body, "https://example.com/blog/test")
    assert "import" not in result
    assert "<Widget" not in result
    assert "Be careful!" in result
    assert "The end." in result
