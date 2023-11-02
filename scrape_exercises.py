import fitz  # PyMuPDF
import re

def find_expression_positions(pdf_path, expression):
    with fitz.open(pdf_path) as doc:
        expression_positions = []
        
        for page_number in range(doc.page_count):
            page = doc[page_number]
            blocks = page.get_text("dict")["blocks"]
            
            for b in blocks:
                for l in b.get("lines", []):
                    for s in l["spans"]:
                        text = s["text"]
                        x0, y0, x1, y1 = s.get("bbox", [0, 0, 0, 0])
                        
                        matches = re.finditer(expression, text)
                        for match in matches:
                            start, end = match.span()
                            matched_text = match.group(0)
                            expression_positions.append({
                                "text": matched_text,
                                "x0": x0,
                                "y0": min(y0, y1),
                                "x1": x1,
                                "y1": max(y0, y1),
                                "page": page_number + 1,
                                "start": start,
                                "end": end,
                                "header": False
                            })
    
    return expression_positions

def get_below_header_positions(pdf_path):
    positions = []
    with fitz.open(pdf_path) as doc:
        for page_number in range(doc.page_count):
            page = doc[page_number]

            if page_number == 0:
                positions.append({
                    "x0": 0,
                    "y0": 220,
                    "x1": page.bound().width,
                    "y1": 220,
                    "page": page_number + 1,
                    "header": True
                })

            else:
                positions.append({
                    "x0": 0,
                    "y0": 50,
                    "x1": page.bound().width,
                    "y1": 50,
                    "page": page_number + 1,
                    "header": True
                })
    return positions

pdf_path = "test_pdf.pdf"
expression = r"\b(?:Exame|Teste)\b"

positions_below_header = get_below_header_positions(pdf_path)
expression_positions = find_expression_positions(pdf_path, expression)

"""
Sort the positions by page number and y0 coordinate
TODO: First exercise wont be extracted, I need to find a way to get the upper margin of the first exercise (use the first appearence of 1.?)
"""

positions = sorted(positions_below_header + expression_positions, key=lambda x: (x["page"], x["y0"]))

"""
Extract an image of everything between the positions (up and down)
Dont extract if there is a non header followed by a header
"""

from PIL import Image
import numpy as np

def extract_image(pdf_path, positions):
    with fitz.open(pdf_path) as doc:
    
        images = []
        
        for i in range(len(positions) - 1):
            pos = positions[i]
            next_pos = positions[i + 1]
            
            if not pos["header"] and next_pos["header"]:
                continue # Skip if a non header is followed by a header

            # Skip if the positions are less than 20 pixels apart
            if abs(pos["y0"] - next_pos["y0"]) < 20:
                continue
            
            page = doc[pos["page"] - 1]
            
            # Extract the image between y0 and y1 of the positions, x0 and x1 are the entire page length
            x0, x1 = 0, int(page.bound().width)
            y0, y1 = int(min(pos["y1"], next_pos["y0"])), int(max(pos["y1"], next_pos["y0"]))
            
            pix = page.get_pixmap(alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = np.array(img)

            img = img[y0:y1, x0:x1]
            images.append(img)
            
        return images

images = extract_image(pdf_path, positions)

# Save images
for i, image in enumerate(images):
    print(image.shape)
    image = Image.fromarray(image)
    image.save(f"exercise_{i}.png")