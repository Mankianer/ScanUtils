#!/bin/bash

# Überprüfe, ob pdftk und zenity installiert sind
for cmd in pdftk; do
    if ! command -v $cmd &> /dev/null; then
        echo "$cmd ist nicht installiert. Möchten Sie es jetzt installieren? (j/n)"
        read -r install
        if [ "$install" = "j" ]; then
            sudo apt-get update
            sudo apt-get install $cmd
        else
            echo "Dieses Skript benötigt $cmd. Bitte installieren Sie es und versuchen Sie es erneut."
            exit 1
        fi
    fi
done

# Zeige Hilfe, wenn keine Argumente gegeben sind
if [ $# -eq 0 ]; then
    echo "Verwendung: $0 [--remove-password|-rm] datei1.pdf datei2.pdf ... dateiN.pdf"
    echo "Verschlüsselt oder entschlüsselt die gegebenen PDF-Dateien mit einem Passwort."
    exit 0
fi

# Entschlüsselungsmodus, falls Parameter --remove-password oder -rm gegeben ist
if [[ $1 == "--remove-password" ]] || [[ $1 == "-rm" ]]; then
    mode="decrypt"
    shift
else
    mode="encrypt"
fi

# Aufforderung zur Eingabe des Passworts
if [ "$mode" == "encrypt" ]; then
    echo "Bitte geben Sie das Passwort ein, mit dem Sie die PDF verschlüsseln möchten: "
else
    echo "Bitte geben Sie das Passwort ein, um die PDF zu entschlüsseln: "
fi
read -rs password

# Durchlaufen Sie alle gegebenen Dateien
for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "Datei $file wurde nicht gefunden."
        continue
    elif [[ $file != *.pdf ]]; then
        echo "$file ist keine PDF-Datei."
        continue
    fi

    if [ "$mode" == "encrypt" ]; then
        if ! pdftk "$file" output "${file%.pdf}_encrypted.pdf" user_pw "$password"; then
            echo "Fehler beim Verschlüsseln von $file"
            continue
        fi

        mv "${file%.pdf}_encrypted.pdf" "$file" && echo "$file wurde erfolgreich verschlüsselt."
    else
        if ! pdftk "$file" input_pw "$password" output "${file%.pdf}_decrypted.pdf"; then
            echo "Fehler beim Entschlüsseln von $file"
            continue
        fi

        mv "${file%.pdf}_decrypted.pdf" "$file" && echo "$file wurde erfolgreich entschlüsselt."
    fi
done
read -p "Press enter to continue"

