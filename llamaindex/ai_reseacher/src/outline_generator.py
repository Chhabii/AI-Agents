def generate_default_outline(papers):

    outline = """
# Research Paper Report

## 1. Introduction:

## 2. Latest Papers:
"""
    # adding each paper to the summary section
    for idx, paper in enumerate(papers, start=1):
        outline += f"\n2.{idx}. {paper['title']}"

    outline += """

## 3. Conclusion:
"""
    return outline
