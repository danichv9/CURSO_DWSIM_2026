# Syngas Lab

Página educativa en español con una ANN real entrenada sobre el Excel adjunto. Abre `Syngas_Lab.html` en cualquier navegador moderno: contiene estilos, código y pesos, funciona sin conexión y no envía entradas a servicios externos. También puedes publicar el contenido de `web/` en un alojamiento estático.

## Utilización

Introduce C, H, O, humedad, cenizas, FC, VM, ER, T y SB; pulsa **Predecir calidad del syngas**. Se muestran H₂, CO, CO₂, CH₄ y LHV, relación H₂/CO y métricas del modelo. Puedes cargar ejemplos del Excel y descargar el experimento en JSON. Los resultados deben recalcularse tras cambiar entradas.

Unidades según la tabla suministrada: C/H/O/Ash/FC/VM en % masa, base seca; humedad total en %; ER adimensional; T en K; SB en kg/kg. H₂/CO/CO₂/CH₄ en % vol., base libre de N₂; LHV en MJ/Nm³. No se efectúan conversiones ni se normalizan composiciones para forzar suma 100. La descripción de humedad se conserva como total; no se inventa una conversión de base.

## Modelo y validación

Arquitectura del notebook: 10 entradas → 10 neuronas tanh → 5 salidas lineales, Adam, lote 16, máximo 400 épocas, parada temprana con paciencia 30 y recuperación de mejores pesos; semilla 42. Hoja1 tiene 274 registros: 164 entrenamiento, 55 validación, 55 prueba. Hoja2 tiene 26 registros externos y jamás se utiliza para ajustar pesos ni escaladores. MinMaxScaler se ajusta únicamente sobre entrenamiento para entradas y salidas. Se conservaron las filas y se limpiaron espacios de los nombres de columnas.

Los pesos se entrenaron de nuevo: los adjuntos no incluían archivos de pesos ni escaladores. El orden de barajado usa tf.data con semilla 42 y un pool de hilos pequeño para el entorno; no se promete igualdad exacta con la ejecución original del notebook. Las métricas reales de esta ejecución aparecen en la interfaz y en `web/model.js`. Las unidades no intervienen en el ajuste: se usan los números del Excel tal como están.

`model.keras` conserva la red; `web/model.js` incluye pesos y límites de ambos escaladores, suficientes para inferencia sin Python. `reference_predictions.json` contiene predicciones TensorFlow para verificar la inferencia del navegador en las 26 muestras externas.

El modelo no impone balances físicos. La aplicación avisa de extrapolaciones y salidas inconsistentes; muestra valores originales sin recortarlos. Los rangos individuales no garantizan que una combinación haya sido observada. No hay umbrales acordados para clasificar el syngas como bueno/malo ni intervalos de confianza. Es una herramienta educativa, no un sistema validado para diseñar u operar una instalación.

## Desarrollo

Desde esta carpeta:

```sh
python3 -m http.server 5174 --bind 127.0.0.1 --directory web
```

Para reentrenar, instala `requirements-training.txt` en un entorno virtual y ejecuta `python train.py`. La página no necesita esas dependencias. El archivo HTML autónomo se genera con `python package_site.py` después de actualizar el modelo o la interfaz. Los datos y notebook originales están en `data/`.
