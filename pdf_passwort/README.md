# PDF Password Script
Dieses Repository beinhaltet zwei Skripte - `pdf_passwort.sh` und `pdf_passwort.bat` - zum Verschlüsseln und Entschlüsseln von PDF-Dateien mittels Passworteingabe. Das Bash-Skript `pdf_passwort.sh` führt die eigentliche Verschlüsselung/Entschlüsselung durch, während das Batch-Skript `pdf_passwort.bat` zum Ausführen des Bash-Skripts in der Windows Subsystem for Linux (WSL) Umgebung dient. Das Batch-Skript unterstützt außerdem das Ziehen und Ablegen (Drag & Drop) von PDF-Dateien.

## Voraussetzungen
- Windows Subsystem for Linux (WSL) muss auf Ihrem System installiert sein.
- Die `pdftk` Software muss in Ihrem WSL installiert sein. Wenn sie nicht installiert ist, wird das Skript Sie bei der Ausführung fragen, ob es sie für Sie installieren soll.

## Verwendung
1. Ziehen Sie die zu verschlüsselnden oder entschlüsselnden PDF-Dateien auf das `pdf_passwort.bat`-Symbol. Das Skript wird automatisch in WSL ausgeführt.

2. Es wird Sie gefragt, ob Sie den Modus auswählen möchten (1 für Verschlüsseln, 2 für Entschlüsseln). Geben Sie die entsprechende Nummer ein und drücken Sie die Eingabetaste.

3. Geben Sie das Passwort ein, mit dem Sie die PDF-Datei verschlüsseln möchten (falls Sie den Verschlüsselungsmodus gewählt haben), oder das Passwort, mit dem die PDF-Datei entschlüsselt werden soll (falls Sie den Entschlüsselungsmodus gewählt haben).

Die verschlüsselten oder entschlüsselten Dateien ersetzen die Originaldateien. Bei erfolgreicher Ausführung wird eine Bestätigungsnachricht angezeigt.

## Hinweis
Das Skript kann mehrere PDF-Dateien gleichzeitig verarbeiten. Stellen Sie sicher, dass Sie die richtigen Dateien auswählen, da die Originaldateien ersetzt werden.

## Fehlerbehebung
Falls das Skript auf Probleme stößt, z.B. wenn eine Datei nicht gefunden wird oder das angegebene Passwort falsch ist, gibt es eine entsprechende Fehlermeldung aus und verarbeitet die nächsten Dateien.

