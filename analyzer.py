"""CSV validation and text analysis for ResearchMap."""

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


COLUMNS = ("title", "abstract", "year")
MAX_PAPERS = 500


def load_papers(path: str | Path) -> pd.DataFrame:
    """Read a UTF-8 CSV and return a clean, zero-indexed paper table."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as stream:
            rows = csv.reader(stream, strict=True)
            header = next((row for row in rows if row), None)
            if header is None:
                raise ValueError("This CSV is empty. Add a header and at least one paper.")

            columns = [column.strip().lower() for column in header]
            missing = [column for column in COLUMNS if column not in columns]
            if missing:
                raise ValueError(f"Missing required columns: {', '.join(missing)}.")
            if len(set(columns)) != len(columns):
                raise ValueError("Column names must be unique.")

            records = []
            for row in rows:
                if not row:
                    continue
                if len(row) != len(columns):
                    raise ValueError(f"The CSV could not be parsed near line {rows.line_num}. Check the number of fields.")
                records.append(row)
                if len(records) > MAX_PAPERS:
                    raise ValueError(f"Import up to {MAX_PAPERS} papers at a time.")
    except UnicodeError as error:
        raise ValueError("Save the file as a UTF-8 CSV and try again.") from error
    except csv.Error as error:
        raise ValueError("The CSV could not be parsed. Check commas and quotation marks.") from error
    except OSError as error:
        raise ValueError(f"Could not open the file. {error.strerror or error}") from error

    papers = pd.DataFrame(records, columns=columns)
    if papers.empty:
        raise ValueError("The CSV has a header but no paper records.")

    papers = papers.loc[:, list(COLUMNS)].fillna("")
    papers = papers.apply(lambda column: column.str.strip())
    empty_titles = papers.index[papers["title"].eq("")]
    if len(empty_titles):
        raise ValueError(f"Paper record {empty_titles[0] + 1} needs a title.")

    years = papers["year"]
    invalid_years = papers.index[~(years.eq("") | years.str.fullmatch(r"[0-9]{4}"))]
    if len(invalid_years):
        raise ValueError(f"Use a four-digit year or leave it blank in paper record {invalid_years[0] + 1}.")
    return papers


@dataclass
class Analysis:
    keywords: pd.DataFrame
    similarity: pd.DataFrame | None
    average_similarity: float | None

    def related_papers(self, paper_index: int, limit: int = 3) -> pd.Series:
        """Return the highest-scoring peers, with ties in import order."""
        if self.similarity is None or pd.isna(self.similarity.loc[paper_index, paper_index]):
            return pd.Series(dtype=float)
        return (
            self.similarity.loc[paper_index]
            .drop(index=paper_index)
            .dropna()
            .sort_values(ascending=False, kind="stable")
            .head(limit)
        )


def analyze_papers(papers: pd.DataFrame) -> Analysis:
    """Rank terms by mean TF-IDF and compare papers with cosine similarity."""
    documents = papers["title"].fillna("") + " " + papers["abstract"].fillna("")
    vectorizer = TfidfVectorizer(stop_words="english", strip_accents="unicode")
    try:
        vectors = vectorizer.fit_transform(documents)
    except ValueError as error:
        if "empty vocabulary" not in str(error):
            raise
        return Analysis(pd.DataFrame(columns=["keyword", "mean_tfidf"]), None, None)

    keywords = pd.DataFrame({
        "keyword": vectorizer.get_feature_names_out(),
        "mean_tfidf": vectors.mean(axis=0).A1,
    }).sort_values(["mean_tfidf", "keyword"], ascending=[False, True], ignore_index=True)

    scores = cosine_similarity(vectors).clip(0, 1)
    has_terms = vectors.getnnz(axis=1) > 0
    # A paper with a zero vector has no defined cosine similarity.
    scores[~has_terms, :] = float("nan")
    scores[:, ~has_terms] = float("nan")
    similarity = pd.DataFrame(scores, index=papers.index, columns=papers.index)

    # Count each pair once and exclude all self-comparisons.
    pairs = [
        similarity.iat[row, column]
        for row in range(len(papers)) if has_terms[row]
        for column in range(row) if has_terms[column]
    ]
    average = float(sum(pairs) / len(pairs)) if pairs else None
    return Analysis(keywords, similarity, average)
