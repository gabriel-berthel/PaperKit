def chunk_paragraphs(
    paragraphs: list[str],
    max_words: int = 350,
    overlap: int = 50
) -> list[str]:
    """
    Splits a list of paragraphs into overlapping chunks based on word count.

    Uses a sliding window approach where each chunk contains up to `max_words`
    words, and consecutive chunks overlap by `overlap` words to preserve context
    across boundaries.

    Args:
        paragraphs: Input paragraphs to be chunked.
        max_words: Maximum number of words per chunk.
        overlap: Number of words shared between consecutive chunks.

    Returns:
        A list of text chunks preserving local continuity via overlap.
    """
    
    chunks, current, count = [], [], 0
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        words = len(p.split())
        if count + words > max_words and current:
            chunks.append(' '.join(current))
            # Roll back by overlap words
            overlap_text, overlap_count = [], 0
            for p_back in reversed(current):
                w = len(p_back.split())
                if overlap_count + w > overlap:
                    break
                overlap_text.insert(0, p_back)
                overlap_count += w
            current, count = overlap_text, overlap_count
        current.append(p)
        count += words
        i += 1
    
    if current:
        chunks.append(' '.join(current))
    
    return chunks

