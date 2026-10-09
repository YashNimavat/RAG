"""C1 'artifact zoo': a small synthetic PDF (TOY ILLUSTRATION) whose true text is known, so each extraction
artifact can be measured against ground truth. Built with PyMuPDF only; no external files.

Pages (1-based):
  1  running header + footer; TWO COLUMNS written line by line across the page (as some producers do);
     a word hyphenated at a line end ("extrac-" / "tion"); a line with two ligature glyphs (U+FB01, U+FB02)
  2  running header + footer; a 3 x 2 table drawn with ruling lines
  3  empty (nothing on the page)
  4  "scanned": one image of a sentence, no text layer
  5  running header + footer; one paragraph
Used by c1_measure.py and copied verbatim into the setup cell of labs/C1_parsing_lab.ipynb.
"""
import pymupdf as fitz

ZOO_HEADER = "ACME Technical Report"
ZOO_LEFT = ["Parsing comes before chunking:", "a bad parse cannot be fixed", "by any later extrac-", "tion or retrieval step."]
ZOO_RIGHT = ["Two-column pages are common", "in research papers, and the", "reading order must follow", "each column top to bottom."]
ZOO_LIG = "The \ufb01rst \ufb02ag: check every \ufb01le."
ZOO_TABLE = [["Model", "Max tokens"], ["MiniLM-L6", "256"], ["bge-small", "512"]]
ZOO_SCAN = "This sentence exists only as pixels."
ZOO_P5 = ["Page five checks the text extraction", "and repeats the header and footer."]


def build_zoo(path):
    doc = fitz.open()
    lig_font = fitz.Font("cjk")            # a built-in font that has the ligature glyphs

    def frame(page, n):
        page.insert_text((72, 50), ZOO_HEADER, fontname="helv", fontsize=9)
        page.insert_text((72, 800), f"Page {n}", fontname="helv", fontsize=9)

    p = doc.new_page(width=595, height=842)          # page 1
    frame(p, 1)
    y = 100
    for a, b in zip(ZOO_LEFT, ZOO_RIGHT):            # line by line ACROSS the columns
        p.insert_text((72, y), a, fontname="helv", fontsize=10)
        p.insert_text((320, y), b, fontname="helv", fontsize=10)
        y += 14
    tw = fitz.TextWriter(p.rect)
    tw.append((72, 200), ZOO_LIG, font=lig_font, fontsize=10)
    tw.write_text(p)

    p = doc.new_page(width=595, height=842)          # page 2: ruled table
    frame(p, 2)
    x0, x1, x2, y0, h = 72, 222, 372, 100, 20
    for r, row in enumerate(ZOO_TABLE):
        top = y0 + r * h
        p.draw_rect(fitz.Rect(x0, top, x1, top + h), color=(0, 0, 0), width=0.8)
        p.draw_rect(fitz.Rect(x1, top, x2, top + h), color=(0, 0, 0), width=0.8)
        p.insert_text((x0 + 4, top + 14), row[0], fontname="helv", fontsize=10)
        p.insert_text((x1 + 4, top + 14), row[1], fontname="helv", fontsize=10)

    doc.new_page(width=595, height=842)              # page 3: empty

    src = fitz.open()                                # page 4: an image of text, no text layer
    sp = src.new_page(width=400, height=60)
    sp.insert_text((10, 35), ZOO_SCAN, fontname="helv", fontsize=14)
    pix = sp.get_pixmap(dpi=100)
    p = doc.new_page(width=595, height=842)
    p.insert_image(fitz.Rect(72, 100, 472, 160), pixmap=pix)

    p = doc.new_page(width=595, height=842)          # page 5
    frame(p, 5)
    for i, line in enumerate(ZOO_P5):
        p.insert_text((72, 100 + 14 * i), line, fontname="helv", fontsize=10)
    doc.save(path)
    return path
