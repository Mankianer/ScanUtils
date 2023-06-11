import io
import shutil

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import os
import openai
from fuzzywuzzy import fuzz
import json

# load openai api key
openaiKeyPath = os.path.expanduser('~/.scanner_utils/openai')
with open(openaiKeyPath, 'r') as datei:
    openaiKey = datei.read()
# check if key is present
if openaiKey == "":
    print(f"OpenAI API Key not found. Please enter it in openaiKeyPath: {openaiKeyPath}")
    exit(1)
openai.api_key = openaiKey


def extract_text_from_pdf(pdf_path):
    """
    Diese Funktion extrahiert Text aus einer PDF-Datei und gibt den Text als String zurück.
    :param pdf_path: Pfad zur PDF-Datei.
    :return: String, der den Text der PDF enthält.
    """
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(pdf_path, 'rb') as fh:
        # Nur die ersten beiden Seiten extrahieren
        for page in list(PDFPage.get_pages(fh, caching=True, check_extractable=True))[:1]:
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    # Offene Handles schließen
    converter.close()
    fake_file_handle.close()

    if text:
        return text
    return None


def find_most_frequent_files(directory: str, num_files: int = 10) -> str:
    results = {}

    # Durchläuft jedes Verzeichnis und jede Datei im gegebenen Verzeichnis
    for root, dirs, files in os.walk(directory):
        # Prüft, ob die Datei 'kategorie' existiert
        if 'kategorie' in files:
            # Entfernt die 'kategorie' Datei aus der Dateiliste
            files.remove('kategorie')
            if len(files) > num_files:
                remove_similar(files, num_files)

            # Fügt die Ergebnisse zu den Gesamtergebnissen hinzu
            category = os.path.relpath(root, directory)
            results[category] = ['"' + file + '"' for file in files]

    # Formatiert die Ergebnisse als String
    result_string = "Kategorie: \"Datei1\",\"Datei2\",\"Datei3\"\n"
    for category, files in results.items():
        result_string += f"{category}: {', '.join(files)}\n"

    return result_string


def remove_similar(files, num_files):
    # Bewertet die Ähnlichkeit jedes Dateipaares
    similarity_scores = {}
    for file1 in files:
        for file2 in files:
            if file1 != file2:
                similarity_scores[(file1, file2)] = fuzz.ratio(file1, file2)
    # Entfernt die ähnlichsten Dateien, bis nur noch die gewünschte Anzahl von Dateien übrig ist
    while len(files) > num_files:
        # Findet das Dateipaar mit der höchsten Ähnlichkeit
        most_similar_pair = max(similarity_scores, key=similarity_scores.get)
        # Findet die Datei mit der höchsten Gesamtähnlichkeit
        most_similar_file = max(most_similar_pair, key=lambda file: sum(
            score for (file1, file2), score in similarity_scores.items() if file1 == file or file2 == file))
        # Entfernt die ähnlichste Datei
        files.remove(most_similar_file)
        # Aktualisiert die Ähnlichkeitsbewertungen
        similarity_scores = {(file1, file2): score for (file1, file2), score in similarity_scores.items() if
                             file1 != most_similar_file and file2 != most_similar_file}


def validiere_json(json_string):
    try:
        daten = json.loads(json_string)
        return daten
    except json.JSONDecodeError:
        print("Ungültiges JSON.")
        return None


if __name__ == '__main__':
    dokumente_folder = 'G:/Meine Ablage/Dokumente'
    target_pdf = 'testpdf.pdf'

    kategories_prompt = find_most_frequent_files(dokumente_folder)
    pdf_text = extract_text_from_pdf(target_pdf)
    # erstelle prompt
    system_prompt = f"""
    Wähle ein passenden Titel mit Zeitangabe, um die PDF in einem Dateisystem zu ordnen zu können und Ordne der PDF eine der Kategorien zu!
    {kategories_prompt}
    Antworte im Json-Format mit den Eigenschaften Titel und Kategorie."
    """
    print("Prompt:")
    print(system_prompt)

    # sende prompt an openai
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                   messages=[{"role": "system", "content": system_prompt},
                                                             {"role": "user", "content": f"PDF:{pdf_text}"}])
    print("Chatausgabe:")
    gpt_answer_json = chat_completion.choices[0].message.content
    print(gpt_answer_json)
    # validiere json
    gpt_answer = validiere_json(gpt_answer_json)

    if gpt_answer is not None:
        target_folder = os.path.join(dokumente_folder, gpt_answer["Kategorie"])
        # validiere ob target_folder existiert
        if not os.path.exists(target_folder):
            print(
                f"Der Ordner {target_folder} existiert nicht! ChatGPT hat eine Kateogrie vorgeschlagen, die nicht existiert.")
            exit(1)
        target_file = os.path.join(target_folder, gpt_answer["Titel"])
        # validiere ob target_file mit .pdf endet
        if not target_file.endswith(".pdf"):
            target_file = target_file + ".pdf"
        print("target_file:", target_file)
        # validiere ob target_file bereits existiert
        if os.path.exists(target_file):
            print(f"Die Datei {target_file} existiert bereits! Bitte wählen Sie einen anderen Titel.")
            exit(1)
        # verschiebe pdf in target_file
        shutil.move(target_pdf, target_file)
        print(f"Die Datei {target_file} wurde erfolgreich verschoben!")

    else:
        print("Die Antowrt von ChatGPT konnte nicht als JSON verarbeitet werden!")
