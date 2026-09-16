# Imou Ranger: video și PTZ în Home Assistant

Configurația acestui exemplu:

| Element | Valoare |
| --- | --- |
| Home Assistant / Raspberry Pi | `10.100.1.34` |
| Camera Imou | `10.100.1.201` |
| Stream existent în go2rtc | `imou_ranger` |
| API add-on IMOU Local PTZ | `http://10.100.1.34:8089` |
| API go2rtc, dacă portul este expus în LAN | `http://10.100.1.34:1984` |

Pentru altă rețea, înlocuiește adresele. Nu publica parole în repository.
Add-on-ul IMOU gestionează mișcarea; add-on-ul go2rtc gestionează imaginea.

## 1. Configurează comanda PTZ

În Home Assistant, editează `configuration.yaml` folosind editorul tău de fișiere.
Acesta NU este fișierul de configurare go2rtc și nici configurația add-on-ului IMOU.

```yaml
rest_command:
  imou_ptz:
    url: "http://10.100.1.34:8089/ptz/move?code={{ direction }}&speed=2&duration=0.4"
    method: GET
    timeout: 15
```

Dacă există deja `rest_command:`, adaugă doar `imou_ptz:` sub secțiunea existentă.
Nu șterge comenzile Xiaomi sau alte comenzi. Dacă folosești un fișier inclus prin
`rest_command: !include ...`, adaugă acolo `imou_ptz:` fără cheia exterioară.
Verifică configurația în Developer Tools → YAML și repornește Home Assistant.

## 2. Testează fără video

Deschide Developer Tools → Actions, treci în modul YAML și execută:

```yaml
action: rest_command.imou_ptz
data:
  direction: Right
```

Camera ar trebui să se miște scurt spre dreapta. Direcțiile sunt `Left`, `Right`,
`Up`, `Down` (cu majusculă). Acest test nu depinde de browser sau de go2rtc.

Dacă acțiunea nu apare, verifică YAML-ul și repornirea Home Assistant. Dacă
primești eroare de conexiune, verifică dacă add-on-ul IMOU este pornit și portul
8000/tcp al containerului este mapat pe portul 8089 al gazdei, apoi consultă Log.

## 3. Pregătește cardul video

Instalează **WebRTC Camera (AlexxIT)** din HACS și urmează instrucțiunile sale de
instalare/restart. Adaugă integrarea din Settings → Devices & services → Add
integration → WebRTC. Reîncarcă pagina browserului.

Acest card este separat de add-on-ul go2rtc. Păstrează streamul `imou_ranger`
deja configurat în go2rtc; nu este necesar să copiezi parola RTSP în dashboard.

Exemplul de mai jos presupune că API-ul add-on-ului go2rtc este accesibil de la
Home Assistant la `http://10.100.1.34:1984/`. Verifică expunerea portului în
Network la add-on. Accesul prin Open Web UI/Ingress nu confirmă automat că portul
1984 este expus. Dacă folosești alt port, modifică `server` în card.

## 4. Adaugă cardul în dashboard

Dashboard → Edit → Add card → Manual:

```yaml
type: custom:webrtc-camera
title: Imou Ranger
url: imou_ranger
server: http://10.100.1.34:1984/
media: video
ptz:
  service: rest_command.imou_ptz
  data_left:
    direction: Left
  data_right:
    direction: Right
  data_up:
    direction: Up
  data_down:
    direction: Down
```

Fiecare apăsare trimite o mișcare de aproximativ 0,4 secunde, urmată de oprire.
Nu este un joystick cu mișcare continuă cât ții apăsat. Viteza `2` și durata
`0.4` se modifică în comanda REST, nu în card. Păstrează durata strict pozitivă:
în upstream, durata zero nu produce oprirea automată.

## Probleme frecvente și siguranță

- `Custom element doesn't exist: webrtc-camera`: verifică instalarea HACS,
  adăugarea integrării WebRTC și reîncarcă browserul.
- Stream necunoscut: verifică numele exact `imou_ranger` și serverul go2rtc ales.
- Imagine neagră doar pe laptop: diagnostichează separat codecul și browserul;
  faptul că PTZ funcționează nu confirmă compatibilitatea video.
- Nu expune porturile **1984** sau **8089** pe Internet. API-ul PTZ nu are
  autentificare; API-ul go2rtc poate permite acces la camere/configurație.
- Parola camerei rămâne în configurația privată a add-on-ului și a go2rtc.
- Documentația și exemplele nu aplică automat modificări pe Home Assistant.

## Referințe

- [Home Assistant RESTful Command](https://www.home-assistant.io/integrations/rest_command/)
- [WebRTC Camera: instalare și card](https://github.com/AlexxIT/WebRTC)
- [WebRTC Camera: PTZ](https://github.com/AlexxIT/WebRTC/wiki/PTZ-Config-Examples)
