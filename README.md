# Monitor Cen PL v0.1.1

Polski interfejs Streamlit do monitorowania cen produktów z listy Excel. Źródła retail i marketplace są rozdzielone.

## Format pliku
Wymagana kolumna: `PN`. Opcjonalne: `EAN`, `NAZWA`.

Uwaga: w dołączonym pliku wartości w kolumnie EAN wyglądają jak identyfikatory tekstowe, a nie 13-cyfrowe numery EAN. Aplikacja zachowuje je jako tekst i używa jako pierwszego klucza wyszukiwania.

## Render Free
1. Umieść katalog w repozytorium GitHub.
2. W Render wybierz New > Blueprint.
3. Wskaż repozytorium. Render odczyta `render.yaml`.
4. Po wdrożeniu otwórz adres usługi.

Dane SQLite na darmowym web service nie powinny być traktowane jako trwałe. Raport pobieraj po skanie.

## Lokalnie
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Ważne
Selektory i zabezpieczenia sklepów zmieniają się. Ta wersja najpierw próbuje danych strukturalnych JSON-LD, potem cen widocznych w wynikach. Przestrzegaj regulaminów serwisów i nie zwiększaj częstotliwości skanów agresywnie.

### v0.1.1
- poprawione rzeczywiste kody EAN,
- automatyczna kolejność wyszukiwania: EAN -> PN -> NAZWA,
- EAN przechowywany jako tekst, bez notacji naukowej.
