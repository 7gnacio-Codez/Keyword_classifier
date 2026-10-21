import json
import re
import unicodedata
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Union, Any, Optional

# Instanciamos el logger a nivel de módulo. 
# Si se importa desde otro script, heredará la configuración de logs del script padre.
logger = logging.getLogger(__name__)

class KeywordClassifier:
    def __init__(self, rules: Dict[str, List[str]], normalize_text: bool = True):
        """
        Inicializa el clasificador.
        :param rules: Diccionario con {Categoría: [palabras clave]}
        :param normalize_text: Si es True, ignora tildes y mayúsculas en las reglas y textos.
        """
        logger.debug(f"Inicializando KeywordClassifier con {len(rules)} categorías. Normalización: {normalize_text}")
        
        self.normalize_text = normalize_text
        self.compiled_patterns = {}
        
        for category, keywords in rules.items():
            if self.normalize_text:
                keywords = [self._remove_accents(kw.lower()) for kw in keywords]
            
            # \b asegura límites de palabra. () captura la palabra exacta que hizo match.
            pattern_str = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            flags = re.IGNORECASE if self.normalize_text else 0
            self.compiled_patterns[category] = re.compile(pattern_str, flags)
            logger.debug(f"Categoría '{category}' compilada con {len(keywords)} keywords.")

    @classmethod
    def from_json(cls, json_path: Union[str, Path], normalize_text: bool = True) -> 'KeywordClassifier':
        """
        Instancia la clase directamente leyendo un archivo de configuración JSON.
        """
        path = Path(json_path)
        logger.info(f"Intentando cargar reglas desde: {path}")
        
        if not path.exists():
            logger.error(f"Archivo no encontrado: {path}")
            raise FileNotFoundError(f"No se encontró el archivo de configuración en: {path}")
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                rules = json.load(f)
            logger.info("Reglas cargadas exitosamente desde JSON.")
            return cls(rules, normalize_text)
        except Exception as e:
            logger.error(f"Error al procesar el JSON: {e}")
            raise

    @staticmethod
    def _remove_accents(text: str) -> str:
        """Elimina tildes y caracteres diacríticos."""
        if not isinstance(text, str):
            return ""
        text = unicodedata.normalize('NFD', text)
        return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

    def classify_text(self, text: Optional[str], default: str = "Sin clasificación") -> Dict[str, Any]:
        """
        Clasifica un texto individual y retorna la categoría y la palabra exacta (evidencia).
        """
        if not text or not isinstance(text, str) or not text.strip():
            logger.warning("Se recibió un texto vacío o nulo para clasificar.")
            return {"categoria": default, "keyword_match": None}

        clean_text = self._remove_accents(text.lower()) if self.normalize_text else text
        
        # Logueamos solo los primeros 30 caracteres para no saturar los logs
        logger.debug(f"Analizando texto: '{clean_text[:30]}...'")

        for category, pattern in self.compiled_patterns.items():
            match = pattern.search(clean_text)
            if match:
                keyword = match.group(1)
                logger.info(f"Match encontrado: '{keyword}' -> Categoría: '{category}'")
                return {
                    "categoria": category, 
                    "keyword_match": keyword
                }
                
        logger.debug("No se encontraron coincidencias. Asignando categoría por defecto.")
        return {"categoria": default, "keyword_match": None}

    def process_payload(self, data: List[Dict[str, Any]], text_key: str) -> List[Dict[str, Any]]:
        """
        Procesa una lista de diccionarios,
        agregando los resultados de la clasificación a cada registro.
        """
        logger.info(f"Iniciando procesamiento de payload con {len(data)} registros. Clave de texto: '{text_key}'")
        
        for index, item in enumerate(data):
            texto = item.get(text_key, "")
            logger.debug(f"Procesando registro {index + 1}/{len(data)}")
            
            resultado = self.classify_text(texto)
            item["categoria_asignada"] = resultado["categoria"]
            item["evidencia_match"] = resultado["keyword_match"]
            
        logger.info("Procesamiento de payload finalizado.")
        return data

def main():
    parser = argparse.ArgumentParser(description="Clasificador de texto basado en keywords (JSON).")
    parser.add_argument("frase", type=str, nargs="?", help="La frase que deseas clasificar.")
    parser.add_argument("-c", "--config", type=str, default="config.json", help="Ruta al archivo config.json")
    parser.add_argument("-l", "--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Nivel de detalle de los logs (por defecto: INFO)")
    
    args = parser.parse_args()

    # Configuración de los logs para cuando se ejecuta como script principal
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    ruta_config = Path(args.config)
    if not ruta_config.exists():
        logger.error(f"No se encontró el archivo de configuración en {ruta_config}")
        exit(1)

    # Instanciamos la clase
    clasificador = KeywordClassifier.from_json(ruta_config)

    if args.frase:
        # Modo Consola
        resultado = clasificador.classify_text(args.frase)
        print(json.dumps(resultado, indent=4, ensure_ascii=False))
    else:
        # Modo Demo
        logger.info("Iniciando Modo Demostración")
        
        payload_demo = [
            {"id": "TKT-001", "comentario": "El sistEma tiene una caida terrible."},
            {"id": "TKT-002", "comentario": "Problemas con el COBRO duplicado en mi tarjeta."},
            {"id": "TKT-003", "comentario": None}
        ]
        
        procesado = clasificador.process_payload(payload_demo, text_key="comentario")
        print("\nRESULTADO PAYLOAD:")
        print(json.dumps(procesado, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
