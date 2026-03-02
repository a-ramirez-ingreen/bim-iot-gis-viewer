import React, { useState } from 'react';
import { Upload, Check, Home, RotateCcw } from 'lucide-react';
import axios from 'axios';
import { MapContainer, TileLayer, GeoJSON, useMap, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './styles/main.css';

// Fix for default marker icon in Leaflet with Webpack/Vite
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Component to auto-center map on GeoJSON
const MapUpdater = ({ geojson }) => {
  const map = useMap();
  React.useEffect(() => {
    if (geojson && geojson.features && geojson.features.length > 0) {
      const layer = L.geoJSON(geojson);
      map.fitBounds(layer.getBounds());
    }
  }, [geojson, map]);
  return null;
};

const MapView = ({ geojson }) => {
  if (!geojson) return <p>Cargando datos del mapa...</p>;

  return (
    <div className="glass-panel full-height-map" style={{ padding: 0 }}>
      <MapContainer
        center={[0, 0]}
        zoom={2}
        minZoom={2}
        maxZoom={25}
        style={{ height: '100%', width: '100%' }}
      >
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              maxNativeZoom={19}
              maxZoom={25}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite (Esri)">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution="Tiles &copy; Esri &mdash;"
              maxNativeZoom={19}
              maxZoom={25}
            />
          </LayersControl.BaseLayer>

          <LayersControl.Overlay checked name="BIM Elements">
            {geojson && (
              <GeoJSON
                data={geojson}
                style={() => ({
                  color: '#007aff',
                  weight: 2,
                  fillColor: '#4facfe',
                  fillOpacity: 0.4
                })}
                onEachFeature={(feature, layer) => {
                  if (feature.properties) {
                    const rows = Object.entries(feature.properties)
                      .map(([key, val]) => `
                                                <tr style="border-bottom: 1px solid #eee;">
                                                    <td style="padding: 4px 8px; font-weight: bold; color: #333; background: #f9f9f9;">${key}</td>
                                                    <td style="padding: 4px 8px; color: #555;">${val}</td>
                                                </tr>
                                            `).join('');

                    const popupContent = `
                                            <div style="font-family: sans-serif; font-size: 13px; max-height: 300px; overflow-y: auto;">
                                                <h3 style="margin: 0 0 10px 0; color: #007aff; border-bottom: 2px solid #007aff; padding-bottom: 5px;">Element Properties</h3>
                                                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                                                    <tbody>
                                                        ${rows}
                                                    </tbody>
                                                </table>
                                            </div>
                                        `;
                    layer.bindPopup(popupContent, { maxWidth: 400 });
                  }
                }}
              />
            )}
          </LayersControl.Overlay>
        </LayersControl>

        <MapUpdater geojson={geojson} />
      </MapContainer>
    </div>
  );
};


// Component to handle drag-and-drop file upload
const FileDropZone = ({ id, label, accept, file, setFile, icon, description, color }) => {
  const [dragging, setDragging] = useState(false);
  const fileInputRef = React.useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div
      className={`drop-zone ${dragging ? 'active' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      style={{ borderLeft: `4px solid ${color}` }}
    >
      <div className="drop-zone-icon">
        {icon}
      </div>
      <div className="drop-zone-title">{label}</div>
      <div className="drop-zone-desc">{description || `Arrastra un archivo ${accept} o haz clic aquí`}</div>

      {file && (
        <div className="file-added-indicator animate-fade-in">
          <Check size={14} style={{ marginRight: '4px' }} />
          {file.name.length > 20 ? file.name.substring(0, 17) + '...' : file.name}
        </div>
      )}

      <input
        type="file"
        id={id}
        ref={fileInputRef}
        accept={accept}
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
          }
        }}
        style={{ display: 'none' }}
      />
    </div>
  );
};

const App = () => {
  // Local State
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Data
  const [geojson, setGeojson] = useState(null);
  const [owlData, setOwlData] = useState(null);

  // Inputs
  const [fileIfc, setFileIfc] = useState(null);
  const [fileSensors, setFileSensors] = useState(null);
  const [fileConfig, setFileConfig] = useState(null);

  // --- New Single Process Handler ---
  const handleProcess = async () => {
    if (!fileIfc) {
      alert("Debes seleccionar un archivo IFC como mínimo.");
      return;
    }

    const formData = new FormData();
    formData.append("file_ifc", fileIfc);
    if (fileSensors) formData.append("file_sensors", fileSensors);
    if (fileConfig) formData.append("file_config", fileConfig);

    try {
      setLoading(true);
      const res = await axios.post('http://localhost:8000/api/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (res.data.status === 'success') {
        setGeojson(res.data.geojson);
        setOwlData(res.data.owl);
        setStep(2); // Go to Visualizer (Step 2 in simplified flow)
      } else {
        alert("Error en el procesado (Status != success)");
      }

    } catch (err) {
      console.error(err);
      alert("Error procesando modelo: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadGML = async () => {
    if (!fileIfc) {
      alert("No hay archivo IFC cargado.");
      return;
    }

    const formData = new FormData();
    formData.append("file_ifc", fileIfc);
    if (fileSensors) formData.append("file_sensors", fileSensors);
    if (fileConfig) formData.append("file_config", fileConfig);

    try {
      setLoading(true);
      const res = await axios.post('http://localhost:8000/api/process/inspire-gml', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (res.data.status === 'success' && res.data.bu_gml) {
        // Download GML
        const blob = new Blob([res.data.bu_gml], { type: "application/xml" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = "BU_min.gml";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else {
        alert("Error: No se pudo generar el GML INSPIRE.");
      }

    } catch (err) {
      console.error(err);
      alert("Error generando GML: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const resetToolState = () => {
    setStep(1);
    setFileIfc(null);
    setFileSensors(null);
    setFileConfig(null);
    setGeojson(null);
    setOwlData(null);
  };

  return (
    <div className="container animate-fade-in">
      {/* Header */}
      <div className="tool-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div className="icon-box">
            <Home size={24} color="var(--accent-color)" />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Visor BIM a GIS</h1>
            <p style={{ margin: '5px 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Conversión directa IFC → GeoJSON + OWL
            </p>
          </div>
        </div>
        <div className="tool-header-actions">
          <button onClick={resetToolState} className="btn-icon reset-btn" title="Limpiar todo">
            <RotateCcw size={18} />
            <span>Reiniciar</span>
          </button>
        </div>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>

        {/* STEP 1: INPUTS */}
        {step === 1 && (
          <div className="animate-fade-in" style={{ padding: '40px' }}>

            <div style={{ textAlign: 'center', marginBottom: '40px' }}>
              <h2 style={{ fontSize: '2rem', marginBottom: '10px' }}>Cargar Modelo y Datos</h2>
              <p style={{ color: 'var(--text-secondary)' }}>Arrastra los archivos necesarios para iniciar el procesamiento</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', maxWidth: '1000px', margin: '0 auto' }}>

              {/* 1. Archivo IFC */}
              <FileDropZone
                id="ifc-upload"
                label="1. Archivo IFC"
                accept=".ifc"
                file={fileIfc}
                setFile={setFileIfc}
                color="var(--accent-color)"
                icon={<Upload size={32} />}
                description="Requerido. Modelo geométrico BIM."
              />

              {/* 2. SENSORS (Opcional) */}
              <FileDropZone
                id="sensors-upload"
                label="2. Sensores"
                accept=".json"
                file={fileSensors}
                setFile={setFileSensors}
                color="#ff9f0a"
                icon={<Upload size={32} />}
                description="Opcional. Datos de sensores IoT."
              />

              {/* 3. CONFIG (Opcional) */}
              <FileDropZone
                id="config-upload"
                label="3. Configuración"
                accept=".json"
                file={fileConfig}
                setFile={setFileConfig}
                color="#bf5af2"
                icon={<Upload size={32} />}
                description="Opcional. Parámetros de umbral."
              />

            </div>

            <div style={{ marginTop: '50px', textAlign: 'center' }}>
              <button
                className="btn-primary"
                onClick={handleProcess}
                disabled={loading || !fileIfc}
                style={{ padding: '15px 60px', fontSize: '1.2rem', minWidth: '300px' }}
              >
                {loading ? (
                  <>
                    <div className="spinner" style={{ marginRight: '10px' }}></div>
                    Procesando...
                  </>
                ) : (
                  <>
                    <Check size={20} />
                    PROCESAR MODELO
                  </>
                )}
              </button>
            </div>

          </div>
        )}

        {/* STEP 2: VISUALIZATION */}
        {step === 2 && (
          <div className="animate-fade-in" style={{ padding: '30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0 }}>Visualización GIS</h2>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button className="btn-sm btn-ghost" onClick={resetToolState}>← Volver</button>
              </div>
            </div>

            <MapView geojson={geojson} />

            <div style={{ marginTop: '30px', display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
              <button className="btn-primary" onClick={() => {
                // Download GeoJSON
                const dataStr = JSON.stringify(geojson, null, 2);
                const blob = new Blob([dataStr], { type: "application/geo+json" });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = "bim_gis_model.geojson";
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}>
                <Upload size={18} style={{ transform: 'rotate(180deg)' }} />
                Descargar GeoJSON
              </button>

              {owlData && (
                <button className="btn-secondary" onClick={() => {
                  // Download OWL
                  const blob = new Blob([owlData], { type: "application/rdf+xml" });
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = "bim_gis_ontology.owl";
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}>
                  Descargar OWL
                </button>
              )}

              <button
                className="btn-secondary"
                onClick={handleDownloadGML}
                disabled={loading}
              >
                {loading ? "Generando GML..." : "Descargar INSPIRE GML"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default App;
