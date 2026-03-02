# BIM-IoT-GIS Viewer

**Herramienta de integración para Gemelos Digitales: Transforma modelos BIM (IFC) en GIS (GeoJSON) integrando sensores IoT y semántica OWL. Genera archivos compatibles con INSPIRE GML.**

Esta aplicación facilita la visualización y conversión técnica de modelos de construcción a entornos territoriales interoperables.

## 🚀 Instalación y Uso Rápido (Windows)

Para ejecutar esta herramienta en tu computadora local:

1.  **Requisitos Previos:**
    *   Instala [Python 3.9+](https://www.python.org/downloads/)
    *   Instala [Node.js](https://nodejs.org/) (Versión LTS recomendada)
2.  **Lanzamiento:**
    *   Haz doble clic en el archivo `inicio_rapido.bat`.
    *   El script configurará automáticamente un entorno virtual de Python, instalará las dependencias de Node.js y lanzará tanto el servidor backend como el frontend.
    *   Una vez listo, el visor se abrirá automáticamente en tu navegador predeterminado en `http://localhost:5173`.

## 📂 Estructura del Proyecto

*   `/backend`: API basada en FastAPI para el procesamiento de archivos IFC, generación de ontologías OWL y exportación INSPIRE GML.
*   `/frontend`: Aplicación React + Vite con interfaz moderna `glassmorphism` y soporte Drag-and-Drop.
*   `inicio_rapido.bat`: Script de automatización para Windows.

## 🛠️ Tecnologías Utilizadas

*   **BIM Engine:** IfcOpenShell
*   **GIS Engine:** Leaflet, Shapely, PyProj
*   **Semántica:** RDFLib (OWL)
*   **Modern Web:** React, Vite, Axios, Lucide Icons

---
Desarrollado para la integración eficiente de datos BIM y GIS.
