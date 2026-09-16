# Diagnostic Privacy — numai citire (0.1.2)

Acesta NU este încă un switch Privacy. Verifică doar câteva servicii și nume
candidate de configurare prin DVRIP. Nu trimite comenzi de modificare, mișcare,
restart sau actualizare firmware. Comenzile PTZ existente rămân disponibile.

## Actualizare și rulare

1. În Home Assistant, deschide magazinul de add-on-uri/apps și folosește
   meniul ⋮ → Check for updates (Verifică actualizările).
2. Deschide **IMOU Local PTZ** și actualizează la **0.1.2**. Păstrează configurația.
3. Pornește add-on-ul dacă nu a repornit automat și verifică fila Log.
4. Dintr-un browser aflat în aceeași rețea, deschide:

   `http://10.100.1.34:8089/diagnostics/privacy`

5. Dacă apare `"status": "running"`, așteaptă aproximativ 10–30 secunde și
   reîncarcă pagina. O conexiune lentă poate dura mai mult; nu reporni repetat.
6. Copiază raportul JSON pentru analiză. Nu trimite `/data/options.json`, parola
   camerei sau configurația RTSP.

Diagnosticul pornește numai la prima accesare după pornirea add-on-ului. Nu
rulează automat la boot. Reîncărcările paginii returnează același rezultat, fără
noi interogări. Pentru o nouă rulare, repornește add-on-ul și deschide din nou URL-ul.
Raportul se păstrează numai în memorie.

## Ce interoghează

Lista este fixă, fără parametri RPC trimiși de utilizator:

- `system.listService` — păstrează în raport doar numele câtorva servicii relevante;
- `configManager.getConfig`, nume `LeLensMask`;
- `configManager.getConfig`, nume `LensMask`;
- `configManager.getConfig`, nume `PrivacyMode`.

Aceste nume sunt **ipoteze de verificat**, nu comenzi Privacy confirmate pentru
Ranger 2 sau firmware-ul `2.810.0000000.1.R.251205`. Diagnosticul folosește
autentificarea DVRIP existentă, pe o sesiune/socket separat de PTZ. Unele camere
pot limita numărul de sesiuni și pot refuza această conexiune suplimentară.

## Interpretarea raportului

| Câmp / valoare | Semnificație |
| --- | --- |
| `status: complete` | Interogările s-au încheiat; NU înseamnă că Privacy este suportat. |
| `checks[].status: accepted` | Camera a răspuns `result: true` la citire. Nu confirmă existența unei comenzi de scriere. |
| `checks[].status: rejected` | Camera a respins interogarea; se exportă doar codul numeric al erorii. |
| `status: incomplete` | Timeout, eroare de transport sau răspuns neinterpretabil; celelalte probe nu au mai fost trimise. |
| `status: connection_or_login_failed` | Sesiunea de diagnostic nu a putut fi deschisă/autentificată. |
| `safe_state_fields` | Numai câmpuri simple dintr-o listă permisă; poate fi gol chiar dacă răspunsul conține alte date. |
| `privacy_support: not_determined` | Intenționat: diagnosticul singur nu dovedește funcționarea Privacy. |

Lipsa unui rezultat pozitiv nu dovedește că Privacy local este imposibil.
Nu există încă interpretare garantată pentru toate variantele DVRIP/firmware.
Nu considerăm camera privată doar pentru că un câmp `Enable` apare cu valoarea
`true`: trebuie verificat ce controlează efectiv și comportamentul video/audio.

Raportul nu exportă răspunsuri brute, parole, seria camerei, sesiuni, adrese sau
mesaje de eroare provenite de la cameră. Se păstrează numai câmpuri de stare
permise și coduri numerice. Nu expune portul 8089 pe Internet: API-ul existent
nu este autentificat.

## Verificări de dezvoltare

Teste simulate pentru parserul DVRIP, limite de dimensiune/timp, lista de
interogări permise, filtrarea informațiilor sensibile, rularea unică, ruta HTTP
și păstrarea accesului la health/PTZ în timpul diagnosticului. Nu reprezintă
validare pe o cameră fizică și nici un build ARM64 executat pe HAOS.

Din rădăcina repository-ului, cu sursa upstream la commit-ul fixat în Dockerfile:

```sh
PYTHONPATH=/cale/catre/ptz-imou python3 -m unittest discover -s tests -v
```
