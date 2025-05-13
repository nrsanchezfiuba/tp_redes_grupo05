# tp_redes_grupo05

## Descripción
El objetivo de este trabajo práctico es desarrollar una aplicación de red para comprender la comunicación entre procesos y el modelo de servicio de la capa de transporte hacia la capa de aplicación. Además, se aprenderá a usar la interfaz de sockets y los principios básicos de la transferencia de datos confiable (RDT).

## Integrantes del Grupo

| Nombre            | Legajo  | Email                 |
|-------------------|---------|-----------------------|
| Agustín Barbalase | 109071  | abarbalase@fi.uba.ar  |
| Felipe D'alto     | 110000  | fedalto@fi.uba.ar     |
| Nicolás Sanchez   | 98792   | nrsanchez@fi.uba.ar   |
| Santiago Sevitz   | 107520  | ssevitz@fi.uba.ar     |
| Máximo Utrera     | 109651  | mutrera@fi.uba.ar     |

## Configuración del Proyecto (Primera Vez)

**Aclaración**: para no instalar otras dependencias, debe ejecutarse mediante el entorno como se explica a continuación.

En caso de requerir permisos para ejecutar xterm, ejecutar el siguiente comando:

```bash
xhost +si:localuser:root
```

Para configurar el proyecto por primera vez, ejecute el siguiente comando:
```bash
./mn.sh build
```

## Inicio del Proyecto

Para iniciar el proyecto, utilice el siguiente comando:
```bash
./mn.sh run
```

## Activación de entorno

Para activar el entorno, utilice el siguiente comando:

```bash
source .venv/bin/activate
```

## Instalar plugin de Wireshark

Crear la siguiente carpeta

```bash
mkdir -p ~/.local/lib/wireshark/plugins
```

Una vez copiada, copiar el plugin en ese directorio

```bash
cp ./plugin.lua ~/.local/lib/wireshark/plugins
```

En caso de querer desarrollar el plugin, recomiendo ejecutar los siguintes comandos

Primero eliminamos el plugin si lo copiamos

```bash
rm ~/.local/lib/wireshark/plugins/plugin.lua
```

Segundo, creamos un link hard

```bash
ln ./plugin.lua ~/.local/lib/wireshark/plugins/plugin.lua
```

Luego, cada vez que realizamos un cambio sobre el archivo `./plugin.lua`, ejecutamos
la combinacion de teclas: `Ctrl + Shift + L` (Analyze > Reload Lua plugin) para reflejar
los cambios en Wireshark.

### _Troubleshooting_
Si encuentra inconvenientes al ejecutar el ejecutable `./run_mininet.sh`, intente ejecutarlo con privilegios de administrador utilizando `sudo`.

## Requerimientos
- Docker (versión 20.10 o superior)

### Notas
- Asegúrese de que todas las dependencias estén instaladas antes de ejecutar las pruebas.
- Si encuentra problemas, verifique los permisos o la configuración del entorno virtual.


## Anexo: Fragmentación

- [Fragmentación](./docs/fragmentation.md)
