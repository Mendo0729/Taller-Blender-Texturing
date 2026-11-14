# Entrega - Taller de Blender Texturing

Se trabajaron los tres modulos del PDF \`textura.pdf\` mediante
escenas editables en Blender 5.0.1. Se conservaron intactos los
archivos originales dentro de \`Textures_files/\`.

## Archivos finales

| Archivo Blender | Demostracion |
|---|---|
| \`01_materiales.blend\` | Comparacion de material dielectrico, metalico, fibra de carbono con clearcoat y cubo dividido con dos materiales. |
| \`02_camuflaje.blend\` | Textura procedural con Noise, ColorRamp (interpolacion constante), MixRGB y material con la imagen CamoTexture.png. |
| \`03_mapeo_uv.blend\` | Comparacion de coordenadas UV (ColorGridTexture y camuflaje) con coordenadas Object y proyeccion BOX. |
| \`04_tanque_pbr.blend\` | Modelo del tanque original texturizado con albedo, roughness, normal y metallic suministrados. |

Cada proyecto incluye una imagen PNG con el mismo nombre, generada
directamente mediante el motor Cycles. Las texturas externas estan
empaquetadas en cada archivo \`.blend\` para facilitar su apertura.

## Correspondencia con el PDF

- Modulo 1: colores y multiples materiales; metalico, rugosidad y recubrimiento.
- Modulo 2: nodos Image Texture, Noise Texture, ColorRamp y mezcla de camuflaje.
- Modulo 3: editor UV, coordenadas de textura, nodo Mapping y proyeccion BOX.

## Abrir

1. Abrir un proyecto \`.blend\` en Blender 5.0 o compatible.
2. Usar *Material Preview* o *Rendered* para visualizar los materiales.
3. Revisar el workspace Shading para inspeccionar y modificar los nodos.
4. Pulsar F12 para volver a renderizar la escena.

## Notas tecnicas

Los ejemplos practicos son una implementacion de los conceptos del PDF,
no una transcripcion literal de cada captura del tutorial. Las escenas
iniciales y texturas proceden del repositorio.
