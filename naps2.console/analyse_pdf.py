import io
import shutil
import subprocess
import sys
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import os
import openai
from fuzzywuzzy import fuzz
import json
import argparse


def exit_with_error(error_message: str = "Ein Fehler ist aufgetreten."):
    print(error_message)
    input("Drücke Enter, um das Programm zu beenden.")
    sys.exit(1)


# TODO: create system init (openai api Key, Document folder, etc.)
# check naps2 installation
if shutil.which("naps2.console") is None:
    print('Der Befehl "naps2.console" wurde nicht gefunden. Bitte installieren Sie NAPS2.')
    exit_with_error()

# load openai api key
openaiKeyPath = os.path.expanduser('~/.scanner_utils/openai')
with open(openaiKeyPath, 'r') as datei:
    openaiKey = datei.read()
# check if key is present
if openaiKey == "":
    print(f"OpenAI API Key not found. Please enter it in openaiKeyPath: {openaiKeyPath}")
    exit_with_error()
# TODO: check if key is valid
openai.api_key = openaiKey

# load document folder
document_folder = os.path.expanduser('~/.scanner_utils/docs_path')
with open(document_folder, 'r') as datei:
    document_folder = datei.read()


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
    result_string = ""
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


def prompt_by_pdf_text(pdf_text: str, categories_prompt: str) -> str:
    system_prompt = f"""
            Wähle ein passenden Titel für die PDF.
            Der Titel soll gut für Menschen lesbar sein!
            Der Titel soll eine Zeitangabe enthalten!
            Der Titel muss als Dateiname valide sein!
            Der Titel soll maximal 80 Zeichen lang sein.
            Die Titel sollen sich an den Beispielen orientieren!
            
            Ordne der PDF eine der folgenden Kategorien zu!
            Kategorien mit Beispiel Dateien:
            {categories_prompt}
            ---
            
            Wenn keine passende Kategorie vorhanden ist: Sonstiges
            
            Antworte im Json-Format mit den Eigenschaften Titel und Kategorie! 
            Titel und Kategorie müssen korrekt für JSON escaped werden!
            """

    # sende prompt an openai
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                   messages=[{"role": "system", "content": system_prompt},
                                                             {"role": "user", "content": f"PDF:{pdf_text}"}])
    return chat_completion.choices[0].message.content


def analyse_and_move_pdf(dokumente_folder: str, target_pdf: str):
    # get Kategories und Dateien-Beispiele
    print("Kategorien:")
    categories_prompt = find_most_frequent_files(dokumente_folder)
    print(categories_prompt)

    # get pdf text
    print("pdf_text:")
    pdf_text = extract_text_from_pdf(target_pdf)
    print(pdf_text)

    # get gpt answer
    print("Chatausgabe:")
    gpt_answer_json = prompt_by_pdf_text(pdf_text, categories_prompt)
    print(gpt_answer_json)
    # validiere json
    gpt_answer = validiere_json(gpt_answer_json)

    if gpt_answer is not None:
        # if gpt_answer is valid, move pdf to folder
        move_pdf2docs(dokumente_folder, gpt_answer, target_pdf)
    else:
        print("Die Antowrt von ChatGPT konnte nicht als JSON verarbeitet werden!")
        exit_with_error()


def move_pdf2docs(dokumente_folder, gpt_answer, target_pdf):
    target_folder = os.path.join(dokumente_folder, gpt_answer["Kategorie"])
    # validiere ob target_folder existiert
    if not os.path.exists(target_folder):
        print(
            f"Der Ordner {target_folder} existiert nicht! ChatGPT hat eine Kateogrie vorgeschlagen, die nicht existiert.")
        exit_with_error()
    titel_ = gpt_answer["Titel"].replace("/", "_").replace("\\", "_")
    target_file = os.path.join(target_folder, titel_)
    # validiere ob target_file mit .pdf endet
    if not target_file.endswith(".pdf"):
        target_file = target_file + ".pdf"
    print("target_file:", target_file)
    # validiere ob target_file bereits existiert
    if os.path.exists(target_file):
        print(f"Die Datei {target_file} existiert bereits! Bitte wählen Sie einen anderen Titel.")
        exit_with_error("Die Datei existiert bereits! - Fehler von ChatGPT oder Document wirklich schon vorhanden?")
    # verschiebe pdf in target_file
    shutil.move(target_pdf, target_file)
    print(f"Die Datei {target_file} wurde erfolgreich verschoben!")


def scanpdf(scanned_pdf_path: str, naps2_profile: str = 'CANON P-208II'):
    command = 'naps2.console -o "%s" -p "%s" --force --enableocr' % (scanned_pdf_path, naps2_profile)
    exit_code = run_command(command)
    if exit_code != 0:
        print("Fehler beim Scannen der PDF-Datei.")
        exit_with_error()


def ocr_scan(pdf_path: str):
    command = 'naps2.console -n 0 -i "%s" -o "%s" --enableocr --force' % (pdf_path, pdf_path)
    exit_code = run_command(command)
    if exit_code != 0:
        print("Fehler beim Scannen der PDF-Datei.")
        exit_with_error()


def run_command(command: str):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"Fehler beim Ausführen des Befehls: {command}")
            print(f"Fehlerausgabe: {stderr.decode('utf-8')}")

        return process.returncode
    except Exception as e:
        print(f"Ausnahme beim Ausführen des Befehls: {command}")
        print(f"Ausnahmedetails: {str(e)}")
        return -1


def get_pdfs_by_args():
    # Erstellen Sie den Parser
    parser = argparse.ArgumentParser(description='PDF-Dateien die verarbeitet werden sollen.')
    # Fügen Sie die Argumente hinzu
    parser.add_argument('pdf_files', metavar='P', type=str, nargs='+',
                        help='ein Pfad zu einer Datei')
    # Parsen Sie die Argumente
    args = parser.parse_args()

    # Jetzt können Sie auf die Dateipfade zugreifen über args.Dateipfade, das ist eine Liste von Strings
    return args.pdf_files


def process_pdf(pdf_file: str, dokumente_folder: str):
    print("OCR-Scan wird gestartet...")
    ocr_scan(pdf_file)
    # TODO: Frage ob PDF sensibel ist => wenn ja passwort setzen & nicht gpt => manuelle eingabe von titel und kategorie
    analyse_and_move_pdf(dokumente_folder, pdf_file)


if __name__ == '__main__':
    # read arguments
    pdf_files = get_pdfs_by_args()
    # process pdfs
    for pdf_file in pdf_files:
        print(pdf_file)
        process_pdf(pdf_file, document_folder)
    input("Drücke Enter, um das Programm zu beenden.")
