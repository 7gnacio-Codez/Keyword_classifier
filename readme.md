# Clasificador de Texto por Keywords

Un algoritmo reutilizable para clasificar textos basándose en diccionarios de palabras clave (keywords). 
Está diseñado para ser utilizado tanto desde la línea de comandos (CLI) como importado como módulo

## Características Principales

*   **Sin Dependencias Externas:** Construido con librerías estándar de Python (`re`, `json`, `unicodedata`, `logging`, `argparse`).
*   **Configuración :** Las reglas de negocio (categorías y palabras clave) se gestionan desde un archivo `config.json` independiente.
*   **Normalización:** Ignora automáticamente mayúsculas, minúsculas y tildes/diacríticos (ej. "facturación" = "FACTURACION").
*   **Trazabilidad:** No solo devuelve la categoría, sino que extrae la palabra exacta (`keyword_match`) que activó la regla.
*   **Procesamiento:** Incluye métodos nativos para procesar listas de diccionarios.
*   **Logs Integrados:** Sistema de logging (DEBUG, INFO, WARNING, ERROR) que se hereda si se usa como módulo.

## 📋 Requisitos

*   Python 3.6 o superior.
*   No requiere instalar paquetes vía `pip`.

## Configuración (`config.json`)

Crea un archivo llamado `config.json` en la raíz del proyecto. El formato debe ser un diccionario donde las llaves son las **Categorías** y los valores son listas de **Keywords**:

```json
{
    "Soporte TI": ["error", "falla", "caída", "sistema", "vpn"],
    "Facturación": ["pago", "factura", "cobro", "tarjeta"]
}
```

## Uso desde la Consola (CLI)

Puedes ejecutar el script directamente desde tu terminal para pruebas rápidas.

**Uso básico:**
```bash
python classifier.py "Tengo un problema con el cobro de mi tarjeta"
```

**Especificar un archivo de configuración diferente:**
```bash
python classifier.py "La vpn está lenta" -c reglas_especiales.json
```

**Activar el modo depuración - Logs detallados:**
```bash
python classifier.py "No carga la página" --log-level DEBUG
```

## Uso como Módulo en otro Script

El clasificador está diseñado para ser instanciado de forma limpia en otros archivos de Python, sin interferir con tus configuraciones globales o ejecutar código de consola.

```python
import logging
from classifier import KeywordClassifier

# Opcional: Configurar logs de tu script principal
logging.basicConfig(level=logging.INFO)

# 1. Instanciar leyendo el JSON
clasificador = KeywordClassifier.from_json("config.json")

# 2. Clasificar un texto individual
texto = "El sistema arroja pantalla azul"
resultado = clasificador.classify_text(texto)

print(resultado)
# Salida: {'categoria': 'Soporte TI', 'keyword_match': 'sistema'}

# 3. Procesar un lote de datos (Payload)
datos_api = [
    {"id": 1, "mensaje": "Necesito pagar mi boleta"},
    {"id": 2, "mensaje": "Falla en el servidor"}
]

procesados = clasificador.process_payload(datos_api, text_key="mensaje")
print(procesados)
# Cada diccionario ahora incluye 'categoria_asignada' y 'evidencia_match'
```

## Métodos Principales de la Clase

*   `KeywordClassifier.from_json(path)`: Patrón Factory. Crea una instancia leyendo directamente un archivo JSON.
*   `classify_text(text: str)`: Analiza un texto y devuelve un diccionario con la `categoria` y el `keyword_match`. Si no hay coincidencias, devuelve "Sin clasificación".
*   `process_payload(data: list, text_key: str)`: Itera sobre una lista de diccionarios, extrae el texto usando `text_key`, lo clasifica y adjunta los resultados mutando los diccionarios originales.