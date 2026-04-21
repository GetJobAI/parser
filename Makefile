parse-pdf:
	@test -n "$(FILE)" || (echo "Usage: make parse-pdf FILE=path/to/cv.pdf" && exit 1)
	python3 scripts/parse_pdf.py $(FILE)
