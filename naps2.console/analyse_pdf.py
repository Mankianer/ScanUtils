import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import os
import openai

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


if __name__ == '__main__':
    textout = extract_text_from_pdf('testpdf.pdf')
    print("Textausgabe:")
    print(textout)
    # Liste aller Modelle abrufen
    # TODO: Auflistung der Vorhandenen PDFs basierend auf Kategorie
    system_promt = """
    Wähle ein passenden Titel mit Zeitangabe, um die PDF in einem Dateisystem zu ordnen zu können und Ordne der PDF eine der Kategorien zu!
    Kategorien: Arbeit,Versicherung,Schule,Compute,Nicht-Zuordenbar.
    Antworte mit: Titel: "<Titel>", Kategorie: "<Kategorie>"
    """
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                   messages=[{"role": "system", "content": system_promt},
                                                             {"role": "user", "content": f"PDF:{textout}"}])
    print("Chatausgabe:")
    print(chat_completion.choices[0].message.content)
