# Build sample PDFs from Markdown sources
# Requires: uv, typst

SOURCES := article.md report.md book.md
PDFS := $(SOURCES:.md=.pdf)

.PHONY: all clean

all: $(PDFS)

%.pdf: %.md
	uv run md2pdf $<

clean:
	rm -f $(PDFS) $(SOURCES:.md=.typ)
