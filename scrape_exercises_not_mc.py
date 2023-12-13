import fitz  # PyMuPDF
import re
import os
import string 
import random
from PIL import Image
import numpy as np
from json import dump
from requests import get 
from bs4 import BeautifulSoup
import subprocess

# TODO: USE CMD ARGS TO GET THE PDF PATHS AND OPTIONS

s = string.ascii_lowercase + string.ascii_uppercase

# Get the directory of the script
script_directory = os.path.dirname(os.path.realpath(__file__))

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

def get_positions(pdf_path):
    expression = r"\b(?:Exame|Teste)\b"
    positions_below_header = get_below_header_positions(pdf_path)
    expression_positions = find_expression_positions(pdf_path, expression)

    """
    Sort the positions by page number and y0 coordinate
    """

    positions = sorted(positions_below_header + expression_positions, key=lambda x: (x["page"], x["y0"]))
    return positions

def get_bounding_boxes(pdf_path):
    positions = get_positions(pdf_path)
    bboxes = []

    with fitz.open(pdf_path) as doc:
        for i in range(len(positions) - 1):
            pos = positions[i]
            next_pos = positions[i + 1]
            
            if not pos["header"] and next_pos["header"]:
                continue # Skip if a non header is followed by a header

            # Skip if the positions are less than 20 pixels apart
            if abs(pos["y0"] - next_pos["y0"]) < 20:
                continue

            page = doc[pos["page"] - 1]

            x0, x1 = 0, int(page.bound().width)
            y0, y1 = int(min(pos["y1"], next_pos["y0"])), int(max(pos["y0"], next_pos["y1"]))

            bboxes.append({
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "page": pos["page"]
            })

    return bboxes

def extract_images(pdf_path):
    """
    Extract an image of everything between the positions (up and down)
    """

    bboxes = get_bounding_boxes(pdf_path)
    with fitz.open(pdf_path) as doc:
        images = []
        
        for bbox in bboxes:
            zoom = 3    # zoom factor not to lose the quality
            mat = fitz.Matrix(zoom, zoom)
            page = doc[bbox["page"] - 1]
            pix = page.get_pixmap(matrix = mat)
            
            # Extract the image between y0 and y1 of the positions, x0 and x1 are the entire page length
            x0, x1, y0, y1 = bbox["x0"], bbox["x1"], bbox["y0"], bbox["y1"]
            
            pix = page.get_pixmap(alpha=False, matrix=mat, clip=[x0, y0, x1, y1])
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = np.array(img)

            # img = img[y0:y1, x0:x1]
            images.append(img)
            
        return images

def search_for_answer(regex, page, left, top, right, bottom):
    r = fitz.Rect(left, top, right, bottom)  # Define the search region
        
    text = page.get_textpage(clip=r)
    text = text.extractText()

    matches = re.findall(regex, text)
    if matches:
        return matches[0][-1] # Return the last letter of the match (A, B, C or D)

def get_answer(pdf_path):
    bboxes = get_bounding_boxes(pdf_path)
    answers = []
    with fitz.open(pdf_path) as doc:
        for bbox in bboxes:
            page = doc[bbox["page"] - 1]
            answers.append(search_for_answer(r"Resposta: .+ [ABCD]", page, bbox["x0"], bbox["y0"], bbox["x1"], bbox["y1"]))

    answer_jsons = []
    for answer in answers:
        if answer:
            answer_jsons.append(None)
            continue

        l = ["Errei", "Errei", "Errei"]

        opt2, opt3, opt4 = l
        answer_jsons.append({
            "author": "Python",
            "difficulty": 2,
            "answers" : [
                "Acertei",
                opt2,
                opt3,
                opt4
            ]
        })

    return answer_jsons

def get_pdf_links_from_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    _class = "btn btn-small btn-primary btn-sm"
   
    response = get(url, headers=headers)
    html_soup = BeautifulSoup(response.text, 'html.parser')

    # Extract all buttons
    buttons = html_soup.find_all("a", class_=_class)

    # Extract name and link to pdf
    links = []
    for button in buttons:
        if "recursos/exames" in button["href"] or "polinomiais34" in button["href"]:
            continue # skip exams

        links.append({
            "name": button.text,
            "link": "https://mat.absolutamente.net" + button["href"]
        })

    return links

def scrape_exercises(url):
    links = get_pdf_links_from_page(url)

    for i in range(0, len(links)-1, 2):
        exercises = links[i]
        solutions = links[i+1]

        # download the pdfs
        exercises_pdf_path = os.path.join(script_directory, "exercises.pdf")
        solutions_pdf_path = os.path.join(script_directory, "solutions.pdf")

        subprocess.run(["wget", exercises['link'], "-O", "exercises.pdf"])
        subprocess.run(["wget", solutions['link'], "-O", "solutions.pdf"])

        exercises_images = map(Image.fromarray, extract_images("exercises.pdf"))
        solutions_images = map(Image.fromarray, extract_images("solutions.pdf"))
        answers = get_answer("solutions.pdf")

        # Delete the pdfs
        os.remove(exercises_pdf_path)
        os.remove(solutions_pdf_path)

        # Create exercisegroup folder
        folder_path = os.path.join(script_directory, exercises["name"])
        os.makedirs(folder_path, exist_ok=True)

        # Save the images inside the created folder
        for exercise_image, solution_image, answer in zip(exercises_images, solutions_images, answers):
            if not answer:
                continue

            # Create a random name for the exercise folder
            exercise_folder_name = "".join(random.sample(s, 10))
            exercise_folder_path = os.path.join(folder_path, exercise_folder_name)

            # Create the exercise folder
            os.makedirs(exercise_folder_path, exist_ok=True)

            # Save the exercise and solution images
            exercise_image.save(os.path.join(exercise_folder_path, "question.png"))
            solution_image.save(os.path.join(exercise_folder_path, "tip1.png"))

            # Save the answer json
            with open(os.path.join(exercise_folder_path, "info.json"), "w") as f:
                dump(answer, f)

if __name__ == "__main__":
    scrape_exercises("https://mat.absolutamente.net/joomla/index.php/recursos/fichas-de-trabalho/matematica-a")
