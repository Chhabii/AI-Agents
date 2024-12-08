import arxiv
def fetch_papers(tags, num_results):
    papers = []
    for tag in tags.split(","):
        search = arxiv.Search(query=tag.strip(), max_results=num_results, sort_by=arxiv.SortCriterion.SubmittedDate)
        for result in search.results():
            papers.append({
                "id": result.entry_id,
                "title": result.title,
                "authors": ", ".join([author.name for author in result.authors]),
                "url": result.pdf_url,
            })
    return papers
