# 2.3.1 Discovery Phase - API del portal Registraduria

- Fecha UTC: `2026-04-23T22:11:56.968957+00:00`
- Base URL: `https://e14_pres1v_2022.registraduria.gov.co`

## Objetivo

Descubrir y documentar los endpoints reales (XHR/fetch) usados por el portal JS dinamico para navegar departamento -> municipio -> zona -> mesa y descargar PDFs E-14.

## Endpoint de autenticacion detectado

- `GET /auth/csrf`: estado `200`
- Claves del JSON de respuesta: `token`

## Endpoints detectados en scripts del portal

- `POST /auth/csrf` | fuente: `consulta_1.js` | nota: Detectado por regex en JavaScript
- `POST /avanceDepto` | fuente: `consulta_1.js` | nota: Detectado por regex en JavaScript
- `POST /consultarE14` | fuente: `consulta_1.js` | nota: Detectado por regex en JavaScript
- `POST /selectDepto` | fuente: `consulta_1.js` | nota: Detectado por regex en JavaScript
- `POST /selectMpio` | fuente: `consulta_1.js` | nota: Detectado por regex en JavaScript
- `POST /selectZona` | fuente: `consulta_1.js` | nota: Detectado por regex en JavaScript

## Flujo esperado del scraping (resumen)

- 1) Obtener token con `GET /auth/csrf`.
- 2) Solicitar departamentos (normalmente `POST /selectDepto` o flujo equivalente).
- 3) Solicitar municipios con `POST /selectMpio`.
- 4) Solicitar zonas con `POST /selectZona`.
- 5) Solicitar mesas/tokens con `POST /consultarE14`.
- 6) Descargar cada PDF con `POST /descargae14` (campo `data`).

## Nota

Este archivo se regenera automaticamente con `python discovery_phase.py --run-probes`.